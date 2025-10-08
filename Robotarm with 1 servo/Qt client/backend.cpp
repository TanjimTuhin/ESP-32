// Copyright (C) 2022 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

#include "backend.h"
#include "esp32client.h" // Include the header for the network client
#include <QTransform>

Backend::Backend(QObject *parent) : QObject(parent)
{
    // Initialize the connection status property to false
    m_isConnected.setValue(false);

    // --- Existing connections for robot arm UI updates ---
    connect(&m_rotation1Angle, &AnimatedParam::valueChanged, this, &Backend::rot1AngleChanged);
    connect(&m_rotation2Angle, &AnimatedParam::valueChanged, this, &Backend::rot2AngleChanged);
    connect(&m_rotation3Angle, &AnimatedParam::valueChanged, this, &Backend::rot3AngleChanged);
    connect(&m_rotation4Angle, &AnimatedParam::valueChanged, this, &Backend::rot4AngleChanged);
    connect(&m_clawsAngle, &AnimatedParam::valueChanged, this, &Backend::clawsAngleChanged);

    // --- CORRECTED Status Binding ---
    // The status text now depends on the m_isConnected property.
    // When m_isConnected's value changes, this binding will automatically re-evaluate.
    m_status.setBinding([this]() {
        if (m_isCollision.value())
            return QString("Collision!");

        if (m_isConnected.value())
            return QString("Connected to Servo");

        // Check arm animation state
        if (m_rotation1Angle.isRunning() || m_rotation2Angle.isRunning() || m_rotation3Angle.isRunning()
            || m_rotation4Angle.isRunning())
            return QString("Busy");

        // Default state
        return QString("Ready");
    });

    // --- Existing connections for collision detection ---
    connect(&m_rotation1Angle, &AnimatedParam::valueChanged, this, &Backend::detectCollision);
    connect(&m_rotation2Angle, &AnimatedParam::valueChanged, this, &Backend::detectCollision);
    connect(&m_rotation3Angle, &AnimatedParam::valueChanged, this, &Backend::detectCollision);
    connect(&m_rotation4Angle, &AnimatedParam::valueChanged, this, &Backend::detectCollision);
}

Backend::~Backend()
{
    // Ensure we disconnect gracefully when the application closes.
    if (m_espClient) {
        m_espClient->disconnect();
    }
}

// --- Network Functions ---
void Backend::connectToDevice(const QString &ip, int port)
{
    // If we are already connected or trying to connect, disconnect first.
    if (m_espClient) {
        disconnectFromDevice();
    }

    m_espClient = new ESP32Client(ip, port, "IoTDevice2024", this);

    // Update the m_isConnected property based on the client's signals.
    // This will automatically update the status text in the UI.
    connect(m_espClient, &ESP32Client::connectionStateChanged, this, [this](bool connected){
        m_isConnected.setValue(connected);
        if (!connected) {
            // If connection is lost for any reason, clean up the client.
            disconnectFromDevice();
        }
    });

    connect(m_espClient, &ESP32Client::errorOccurred, this, [this](const QString& error){
        m_status.setValue("Error: " + error);
        m_isConnected.setValue(false);
    });

    m_status.setValue("Connecting...");
    m_espClient->connectToHost();
}

void Backend::disconnectFromDevice()
{
    if (m_espClient) {
        m_espClient->disconnect();
        m_espClient->deleteLater(); // Use deleteLater for safe cleanup of QObjects
        m_espClient = nullptr;
    }
    // CORRECTED: Set our property to false. The binding will update the UI status.
    m_isConnected.setValue(false);
}


// --- MODIFIED Setter for Rotation 1 ---
void Backend::setRot1Angle(const int angle)
{
    // This first part is the original logic: it updates the angle for the 3D model.
    m_rotation1Angle.setValue(angle);

    // --- NEW LOGIC: Send data to ESP32 ---
    // Check if the client object exists and is successfully connected.
    if (m_espClient && m_espClient->isConnected()) {
        // Map the slider's range [-90, 90] to the servo's range [0, 180].
        int servoAngle = angle + 90;
        m_espClient->controlServo(servoAngle);
    }
}

// --- ALL FUNCTIONS BELOW THIS POINT ARE UNCHANGED ---

int Backend::rotation1Angle() const { return m_rotation1Angle.value(); }
int Backend::rotation2Angle() const { return m_rotation2Angle.value(); }
void Backend::setRot2Angle(const int angle) { m_rotation2Angle.setValue(angle); }
int Backend::rotation3Angle() const { return m_rotation3Angle.value(); }
void Backend::setRot3Angle(const int angle) { m_rotation3Angle.setValue(angle); }
int Backend::rotation4Angle() const { return m_rotation4Angle.value(); }
void Backend::setRot4Angle(const int angle) { m_rotation4Angle.setValue(angle); }
int Backend::clawsAngle() const { return m_clawsAngle.value(); }
void Backend::setClawsAngle(const int angle) { m_clawsAngle.setValue(angle); }
QString Backend::status() const { return m_status; }
QBindable<QString> Backend::bindableStatus() const { return &m_status; }

void Backend::detectCollision()
{
    // simple aproximate collision detection, uses hardcoded model dimensions
    QPolygon pol1(QRect(-70, 0, 70, 300));
    QTransform t;
    t.rotate(8.7);
    t.translate(0, 259);
    t.rotate(-20.);
    t.rotate(rotation3Angle());
    QPolygon pol2 = t.mapToPolygon(QRect(-35, 0, 35, 233));
    t.translate(0, 233);
    t.rotate(15);
    t.rotate(rotation2Angle());
    QPolygon pol3 = t.mapToPolygon(QRect(-27, 0, 27, 212));
    t.translate(0, 212);
    t.rotate(rotation1Angle());
    QPolygon pol4 = t.mapToPolygon(QRect(-42, 0, 42, 180));
    m_isCollision.setValue(pol1.intersects(pol3) || pol1.intersects(pol4) || pol2.intersects(pol4));
}

