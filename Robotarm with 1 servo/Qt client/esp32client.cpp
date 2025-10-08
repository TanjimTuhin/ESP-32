#include "esp32client.h"
#include <QDebug>
#include <QJsonDocument>
#include <QJsonObject>

ESP32Client::ESP32Client(const QString &host, int port, const QString &authPassword, QObject *parent)
    : QObject(parent)
    , socket(new QTcpSocket(this))
    , host(host)
    , port(port)
    , authPassword(authPassword)
    , authenticated(false)
{
    connect(socket, &QTcpSocket::connected, this, &ESP32Client::onSocketConnected);
    connect(socket, &QTcpSocket::disconnected, this, &ESP32Client::onSocketDisconnected);
    connect(socket, QOverload<QAbstractSocket::SocketError>::of(&QAbstractSocket::errorOccurred),
            this, &ESP32Client::onSocketError);
    connect(socket, &QTcpSocket::readyRead, this, &ESP32Client::onDataReceived);
}

ESP32Client::~ESP32Client()
{
    disconnect();
}

void ESP32Client::connectToHost()
{
    if (socket->state() != QAbstractSocket::UnconnectedState) {
        socket->disconnectFromHost();
        if (socket->state() != QAbstractSocket::UnconnectedState) {
            socket->waitForDisconnected(3000);
        }
    }

    authenticated = false;
    messageBuffer.clear();
    socket->connectToHost(host, port);
}

void ESP32Client::disconnect()
{
    if (socket->state() != QAbstractSocket::UnconnectedState) {
        socket->disconnectFromHost();
        if (socket->state() != QAbstractSocket::UnconnectedState) {
            socket->waitForDisconnected(3000);
        }
    }
    authenticated = false;
}

bool ESP32Client::isConnected() const
{
    return socket->state() == QAbstractSocket::ConnectedState && authenticated;
}

void ESP32Client::controlServo(int angle)
{
    if (!isConnected()) return;

    QJsonObject message;
    message["command"] = "set_servo";
    message["angle"] = angle;
    sendMessage(message);
}

void ESP32Client::onSocketConnected()
{
    QTimer::singleShot(500, this, &ESP32Client::authenticate);
}

void ESP32Client::onSocketDisconnected()
{
    authenticated = false;
    emit connectionStateChanged(false);
}

void ESP32Client::onSocketError(QAbstractSocket::SocketError error)
{
    QString errorString;
    switch (error) {
    case QAbstractSocket::HostNotFoundError:
        errorString = "Host not found. Please check the IP address.";
        break;
    case QAbstractSocket::ConnectionRefusedError:
        errorString = "Connection refused. Make sure the ESP32 is running and accessible.";
        break;
    case QAbstractSocket::RemoteHostClosedError:
        errorString = "ESP32 closed the connection.";
        break;
    case QAbstractSocket::NetworkError:
        errorString = "Network error occurred.";
        break;
    default:
        errorString = socket->errorString();
        break;
    }
    emit errorOccurred(errorString);
}

void ESP32Client::onDataReceived()
{
    QByteArray data = socket->readAll();
    messageBuffer += QString::fromUtf8(data);

    while (messageBuffer.contains('\n')) {
        int newlinePos = messageBuffer.indexOf('\n');
        QString line = messageBuffer.left(newlinePos).trimmed();
        messageBuffer.remove(0, newlinePos + 1);

        if (line.isEmpty()) continue;

        QJsonParseError error;
        QJsonDocument doc = QJsonDocument::fromJson(line.toUtf8(), &error);

        if (error.error == QJsonParseError::NoError && doc.isObject()) {
            processMessage(doc.object());
        }
    }
}

void ESP32Client::sendMessage(const QJsonObject &message)
{
    if (socket->state() != QAbstractSocket::ConnectedState) return;

    QJsonDocument doc(message);
    QByteArray data = doc.toJson(QJsonDocument::Compact) + "\n";
    socket->write(data);
}

void ESP32Client::processMessage(const QJsonObject &message)
{
    if (message.contains("status")) {
        QString status = message["status"].toString();
        if (status == "success" && !authenticated) {
            authenticated = true;
            emit connectionStateChanged(true);
        } else if (status == "error") {
            QString errorMsg = message["message"].toString();
            emit errorOccurred("ESP32 Error: " + errorMsg);
            if (!authenticated) {
                socket->disconnectFromHost();
            }
        }
    }
}

void ESP32Client::authenticate()
{
    if (socket->state() != QAbstractSocket::ConnectedState) return;

    QJsonObject authMessage;
    authMessage["command"] = "auth";
    authMessage["password"] = authPassword;
    sendMessage(authMessage);
}
