#include <WiFi.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "Spectrum Eng.";
const char* password = "Secl@2021";
const int serverPort = 8080; // Match the Qt app's default port

// --- MODIFIED FOR 4 SERVOS ---
const int NUM_SERVOS = 4;
Servo myServos[NUM_SERVOS];
// Assign GPIO pins for each servo. Make sure these pins are not used by other components.
const int servoPins[NUM_SERVOS] = {23, 22, 21, 19}; 

// TCP Server
WiFiServer server(serverPort);
WiFiClient client;

// Authentication
const String requiredPassword = "IoTDevice2024";
bool clientAuthenticated = false;

void setup() {
    Serial.begin(115200);

    // --- MODIFIED FOR 4 SERVOS ---
    // Initialize all servos
    for (int i = 0; i < NUM_SERVOS; i++) {
        myServos[i].attach(servoPins[i]);
        myServos[i].write(90); // Start all servos at 90 degrees
    }
    Serial.println("All 4 servos initialized.");
    
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
        // --- MODIFIED FOR 4 SERVOS ---
        } else if (strcmp(command, "set_servo") == 0) {
            if (clientAuthenticated) {
                // Get the servo index (0-3) and angle from the JSON message
                int servo_index = doc["servo_index"];
                int angle = doc["angle"];

                // Validate the servo index and angle
                if (servo_index >= 0 && servo_index < NUM_SERVOS && angle >= 0 && angle <= 180) {
                    myServos[servo_index].write(angle);
                    Serial.printf("Servo %d moved to %d degrees\n", servo_index, angle);
                    client.println("{\"status\":\"success\"}");
                } else {
                     client.println("{\"status\":\"error\",\"message\":\"Invalid servo index or angle\"}");
                }
            } else {
                Serial.println("Command rejected: client not authenticated.");
                client.println("{\"status\":\"error\",\"message\":\"Not authenticated\"}");
            }
        }
    }
}