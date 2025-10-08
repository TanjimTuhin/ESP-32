#include <WiFi.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h> // You will need to install this library

// WiFi credentials
const char* ssid = "Spectrum Eng.";
const char* password = "Secl@2021";
const int serverPort = 8080; // Match the Qt app's default port

// Servo setup
Servo myServo;
const int servoPin = 23;

// TCP Server
WiFiServer server(serverPort);
WiFiClient client;

// Authentication
const String requiredPassword = "IoTDevice2024";
bool clientAuthenticated = false;

void setup() {
    Serial.begin(115200);

    // Initialize servo
    myServo.attach(servoPin);
    myServo.write(90); // Start at 90 degrees
    
    // Connect to WiFi
    Serial.print("Connecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());

    // Start the server
    server.begin();
    Serial.printf("TCP server started on port %d\n", serverPort);
}

void loop() {
    // Check if a new client has connected
    if (!client.connected()) {
        client = server.available();
        if (client) {
            Serial.println("New client connected!");
            clientAuthenticated = false; // Reset authentication status for new client
        }
        return;
    }

    // Check for incoming data from the client
    if (client.available()) {
        String line = client.readStringUntil('\n');
        Serial.print("Received: ");
        Serial.println(line);

        // Use ArduinoJson to parse the message
        JsonDocument doc;
        DeserializationError error = deserializeJson(doc, line);

        if (error) {
            Serial.print("deserializeJson() failed: ");
            Serial.println(error.c_str());
            // Send error response back to client
            client.println("{\"status\":\"error\",\"message\":\"Invalid JSON\"}");
            return;
        }

        // Process the command
        const char* command = doc["command"];

        if (strcmp(command, "auth") == 0) {
            String password = doc["password"];
            if (password == requiredPassword) {
                clientAuthenticated = true;
                Serial.println("Client authenticated successfully.");
                client.println("{\"status\":\"success\",\"message\":\"Authenticated\"}");
            } else {
                Serial.println("Authentication failed.");
                client.println("{\"status\":\"error\",\"message\":\"Authentication failed\"}");
                client.stop();
            }
        } else if (strcmp(command, "set_servo") == 0) {
            if (clientAuthenticated) {
                int angle = doc["angle"];
                if (angle >= 0 && angle <= 180) {
                    myServo.write(angle);
                    Serial.printf("Servo moved to %d degrees\n", angle);
                    client.println("{\"status\":\"success\"}");
                } else {
                     client.println("{\"status\":\"error\",\"message\":\"Invalid angle\"}");
                }
            } else {
                Serial.println("Command rejected: client not authenticated.");
                client.println("{\"status\":\"error\",\"message\":\"Not authenticated\"}");
            }
        }
    }
}