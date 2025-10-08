#ifndef ESP32CLIENT_H
#define ESP32CLIENT_H

#include <QObject>
#include <QTcpSocket>
#include <QTimer>
#include <QJsonObject>

class ESP32Client : public QObject
{
    Q_OBJECT

public:
    explicit ESP32Client(const QString &host, int port = 8080,
                         const QString &authPassword = "IoTDevice2024",
                         QObject *parent = nullptr);
    ~ESP32Client();

    void connectToHost();
    void disconnect();
    bool isConnected() const;
    void controlServo(int angle);

signals:
    void connectionStateChanged(bool connected);
    void errorOccurred(const QString &error);

private slots:
    void onSocketConnected();
    void onSocketDisconnected();
    void onSocketError(QAbstractSocket::SocketError error);
    void onDataReceived();

private:
    void sendMessage(const QJsonObject &message);
    void processMessage(const QJsonObject &message);
    void authenticate();

    QTcpSocket *socket;
    QString host;
    int port;
    QString authPassword;
    bool authenticated;
    QString messageBuffer;
};

#endif // ESP32CLIENT_H
