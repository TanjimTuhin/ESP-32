/*
 * ESP32 IoT Control System - Main Program
 * 
 * Features:
 * - 5 LEDs controllable via network
 * - 5 Push buttons with debouncing (trigger LED sequence when pressed)
 * - 1 Potentiometer controlling servo motor automatically
 * - WiFi Station mode (connects to router)
 * - TCP Socket server with JSON communication
 * - Multi-client support with authentication
 * - Modular design (separate .h and .cpp files)
 * 
 * Network Configuration:
 * - WiFi STA: Connect to existing router
 * - Server: IP assigned by router on port 8080
 * - Auth Password: IoTDevice2024
 * 
 * Hardware Connections:
 * LEDs:     GPIO 2, 4, 5, 18, 19
 * Buttons:  GPIO 12, 13, 14, 15, 16 (with internal pull-up) - trigger LED sequence
 * Pot:      GPIO 34 (ADC1_CH6) - controls servo motor
 * Servo:    GPIO 23 - controlled by potentiometer
 * 
 * Required Libraries:
 * - ArduinoJson (install via Library Manager)
 * - ESP32Servo (install via Library Manager)
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
    Serial.println("    Potentiometer -> Servo Control");
    Serial.println("    Button Press -> LED Sequence");
    Serial.println(line);
    
    // Initialize hardware module
    hardware.init();
    delay(500);
    
    // Initialize communication module
    communication.init();
    delay(500);
    
    // Startup LED sequence
    Serial.println("[MAIN] Running startup LED sequence...");
    hardware.toggleLEDSequence();
    
    Serial.println("\n" + line);
    Serial.println("    ESP32 IoT Control System Ready!");
    Serial.println("    Potentiometer controls servo automatically");
    Serial.println("    Press any button to trigger LED sequence");
    Serial.println(line);
    Serial.println("[MAIN] System initialized successfully!");
    Serial.println();
}

void loop() {
    // Update hardware (read sensors, debounce buttons, update servo)
    hardware.update();
    
    // Check for button presses and trigger LED sequence
    for (int i = 0; i < 5; i++) {
        if (hardware.isButtonPressed(i)) {
            Serial.printf("[MAIN] Button %d pressed - starting LED sequence\n", i + 1);
            
            // Run LED sequence in a non-blocking way
            // Note: This will block the main loop briefly, but it's acceptable for this demo
            hardware.toggleLEDSequence();
        }
    }
    
    // Handle network communication
    communication.update();
    
    // Small delay to prevent overwhelming the system
    delay(1);
    
    // Optional: Print hardware status every 15 seconds for debugging
    static unsigned long lastStatusPrint = 0;
    if (millis() - lastStatusPrint > 15000) {
        hardware.printStatus();
        lastStatusPrint = millis();
    }
}

/*
 * Updated JSON API Documentation:
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
 * 4. Manual servo control (overrides potentiometer temporarily):
 *    Send: {"command":"set_servo","angle":90}
 *    Response: {"status":"success","message":"Servo set to 90 degrees","timestamp":12345}
 *    Note: Potentiometer will take control again on next update
 * 
 * 5. Get system status:
 *    Send: {"command":"get_status"}
 *    Response: Full status JSON (see automatic updates)
 * 
 * 6. Ping test:
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
 *   },
 *   "servo": {
 *     "angle": 90
 *   }
 * }
 * 
 * System Behavior:
 * - Potentiometer continuously controls servo motor position
 * - Button presses trigger LED toggle sequence
 * - Manual servo commands work but potentiometer takes over again
 * - Smooth analog filtering prevents servo jitter
 * - Deadband filtering reduces unnecessary servo movements
 */