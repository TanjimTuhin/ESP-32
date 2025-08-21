#include <WiFi.h>

// WiFi credentials
const char* ssid = "SECL RnD LAB";
const char* password = "SECL@2024";

// LED pin
#define LED_PIN 2

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    while (!Serial); // Wait for serial port to connect
    delay(1000);
    
    Serial.println();
    Serial.println("ESP32 WiFi Diagnostic Tool");
    Serial.println("==========================");
    
    // Initialize LED pin
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);
    
    // Test LED
    Serial.println("Testing LED...");
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(200);
        digitalWrite(LED_PIN, LOW);
        delay(200);
    }
    Serial.println("LED test complete");
    
    // List available networks
    Serial.println("\nScanning for available networks...");
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
    
    int n = WiFi.scanNetworks();
    Serial.println("Scan complete");
    
    if (n == 0) {
        Serial.println("No networks found. Check antenna or positioning.");
    } else {
        Serial.printf("Found %d networks:\n", n);
        Serial.println("Nr | SSID                             | RSSI | CH | Encryption");
        for (int i = 0; i < n; i++) {
            Serial.printf("%2d", i + 1);
            Serial.print(" | ");
            Serial.print(WiFi.SSID(i));
            for (int j = 0; j < 33 - WiFi.SSID(i).length(); j++) Serial.print(" ");
            Serial.print(" | ");
            Serial.printf("%4d", WiFi.RSSI(i));
            Serial.print(" | ");
            Serial.printf("%2d", WiFi.channel(i));
            Serial.print(" | ");
            
            switch (WiFi.encryptionType(i)) {
                case WIFI_AUTH_OPEN:
                    Serial.println("open");
                    break;
                case WIFI_AUTH_WEP:
                    Serial.println("WEP");
                    break;
                case WIFI_AUTH_WPA_PSK:
                    Serial.println("WPA");
                    break;
                case WIFI_AUTH_WPA2_PSK:
                    Serial.println("WPA2");
                    break;
                case WIFI_AUTH_WPA_WPA2_PSK:
                    Serial.println("WPA+WPA2");
                    break;
                case WIFI_AUTH_WPA2_ENTERPRISE:
                    Serial.println("WPA2-EAP");
                    break;
                case WIFI_AUTH_WPA3_PSK:
                    Serial.println("WPA3");
                    break;
                case WIFI_AUTH_WPA2_WPA3_PSK:
                    Serial.println("WPA2+WPA3");
                    break;
                default:
                    Serial.println("unknown");
            }
        }
    }
    
    // Try to connect to WiFi
    Serial.println();
    Serial.printf("Attempting to connect to: %s\n", ssid);
    
    WiFi.begin(ssid, password);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
        digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Blink LED
    }
    
    Serial.println();
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Connected successfully!");
        Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("Subnet mask: %s\n", WiFi.subnetMask().toString().c_str());
        Serial.printf("Gateway: %s\n", WiFi.gatewayIP().toString().c_str());
        Serial.printf("DNS: %s\n", WiFi.dnsIP().toString().c_str());
        Serial.printf("RSSI: %d dBm\n", WiFi.RSSI());
        
        // Solid LED indicates successful connection
        digitalWrite(LED_PIN, HIGH);
    } else {
        Serial.println("Connection failed!");
        Serial.printf("Status code: %d\n", WiFi.status());
        
        // Print status meaning
        switch (WiFi.status()) {
            case WL_IDLE_STATUS:
                Serial.println("WL_IDLE_STATUS: WiFi is in process of changing between statuses");
                break;
            case WL_NO_SSID_AVAIL:
                Serial.println("WL_NO_SSID_AVAIL: SSID cannot be reached");
                break;
            case WL_SCAN_COMPLETED:
                Serial.println("WL_SCAN_COMPLETED: Scan networks is completed");
                break;
            case WL_CONNECTED:
                Serial.println("WL_CONNECTED: Successfully connected to a WiFi");
                break;
            case WL_CONNECT_FAILED:
                Serial.println("WL_CONNECT_FAILED: Password is incorrect");
                break;
            case WL_CONNECTION_LOST:
                Serial.println("WL_CONNECTION_LOST: Connection is lost");
                break;
            case WL_DISCONNECTED:
                Serial.println("WL_DISCONNECTED: Disconnected from a network");
                break;
            default:
                Serial.println("Unknown status");
        }
        
        // Fast blink indicates error
        while (1) {
            digitalWrite(LED_PIN, HIGH);
            delay(100);
            digitalWrite(LED_PIN, LOW);
            delay(100);
        }
    }
}

void loop() {
    // Your network is stable if the LED remains solid
    delay(1000);
    
    // Occasionally print connection status
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 10000) {
        lastPrint = millis();
        Serial.printf("Maintaining connection to %s, RSSI: %d dBm\n", 
                     ssid, WiFi.RSSI());
    }
}