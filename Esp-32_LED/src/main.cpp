/*
 * ESP32 IoT Control System - Main Program
 * 
 * Features:
 * - 5 LEDs controllable via network
 * - 5 Push buttons with debouncing
 * - 1 Potentiometer (analog input)
 * - WiFi Access Point mode
 * - TCP Socket server with JSON communication
 * - Multi-client support with authentication
 * - Modular design (separate .h and .cpp files)
 * 
 * Network Configuration:
 * - WiFi AP: ESP32_IoT_Server / ESP32Pass123
 * - Server: 192.168.4.1:8080
 * - Auth Password: IoTDevice2024
 * 
 * Hardware Connections:
 * LEDs:     GPIO 2, 4, 5, 18, 19
 * Buttons:  GPIO 12, 13, 14, 15, 16 (with internal pull-up)
 * Pot:      GPIO 34 (ADC1_CH6)
 * 
 * Required Libraries:
 * - ArduinoJson (install via Library Manager)
 * 
 * File Structure:
 * - main.ino (this file)
 * - HardwareModule.h
 * - HardwareModule.cpp
 * - CommunicationModule.h
 * - CommunicationModule.cpp
 */

#include "HardwareModule.h"
#include "CommunicationModule.h"

// Global objects
HardwareModule hardware;
CommunicationModule communication(&hardware);
// Helper function to repeat a character
String repeatChar(char c, int count) {
    String result = "";
    for (int i = 0; i < count; i++) {
        result += c;
    }
    return result;
}

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    delay(1000);
    
    String line = repeatChar('=', 50);

    Serial.println("\n" + line);
    Serial.println("    ESP32 IoT Control System Starting...");
    Serial.println(line);
    
    // Initialize hardware module
    hardware.init();
    delay(500);
    
    // Initialize communication module
    communication.init();
    delay(500);
    
    // Startup LED sequence
    Serial.println("[MAIN] Running startup LED sequence...");
    for (int i = 0; i < 5; i++) {
        hardware.setLED(i, true);
        delay(200);
    }
    delay(500);
    for (int i = 0; i < 5; i++) {
        hardware.setLED(i, false);
        delay(200);
    }
    
    Serial.println("\n" + line);
    Serial.println("    ESP32 IoT Control System Ready!");
    Serial.println(line);
    Serial.println("[MAIN] System initialized successfully!");
    Serial.println("[MAIN] Connect to WiFi and use client to control the system.");
    Serial.println();
}

void loop() {
    // Update hardware (read sensors, debounce buttons)
    hardware.update();
    
    // Handle network communication
    communication.update();
    
    // Small delay to prevent overwhelming the system
    delay(10);
    
    // Optional: Print hardware status every 15 seconds for debugging
    static unsigned long lastStatusPrint = 0;
    if (millis() - lastStatusPrint > 15000) {
        hardware.printStatus();
        lastStatusPrint = millis();
    }
}

/*
 * JSON API Documentation:
 * 
 * 1. Authentication (required first):
 *    Send: {"command":"auth","password":"IoTDevice2024"}
 *    Response: {"status":"success","message":"Authenticated","timestamp":12345}
 * 
 * 2. Control single LED:
 *    Send: {"command":"set_led","led":1,"state":true}
 *    Response: {"status":"success","message":"LED 1 set to ON","timestamp":12345}
 * 
 * 3. Control all LEDs:
 *    Send: {"command":"set_all_leds","state":false}
 *    Response: {"status":"success","message":"All LEDs set to OFF","timestamp":12345}
 * 
 * 4. Get system status:
 *    Send: {"command":"get_status"}
 *    Response: Full status JSON (see automatic updates)
 * 
 * 5. Ping test:
 *    Send: {"command":"ping"}
 *    Response: {"status":"success","message":"pong","timestamp":12345}
 * 
 * Automatic Status Updates (every 1 second):
 * {
 *   "type": "status",
 *   "timestamp": 12345,
 *   "leds": [
 *     {"id": 1, "state": false},
 *     {"id": 2, "state": true},
 *     ...
 *   ],
 *   "buttons": [
 *     {"id": 1, "pressed": false},
 *     {"id": 2, "pressed": true},
 *     ...
 *   ],
 *   "potentiometer": {
 *     "raw": 2048,
 *     "voltage": 1.65,
 *     "percent": 50
 *   }
 * }
 */