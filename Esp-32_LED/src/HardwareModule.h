#ifndef HARDWARE_MODULE_H
#define HARDWARE_MODULE_H

#include <Arduino.h>
#include <ESP32Servo.h>

class HardwareModule {
private:
    // GPIO Pin Definitions
    static const int LED_PINS[5];
    static const int BUTTON_PINS[5];
    static const int POTENTIOMETER_PIN = 34; // ADC1_CH6
    static const int SERVO_PIN = 23;

    // Button debouncing
    bool buttonStates[5];
    bool lastButtonStates[5];
    unsigned long lastDebounceTime[5];
    static const unsigned long DEBOUNCE_DELAY = 50;
    
    // Analog reading smoothing
    static const int ANALOG_SAMPLES = 20;  // Increased for better stability
    int analogReadings[ANALOG_SAMPLES];
    int analogIndex;
    long analogTotal;
    
    // Servo object and control
    Servo servoMotor;
    int currentServoAngle;
    int lastPotServoAngle;
    unsigned long lastServoUpdate;
    static const unsigned long SERVO_UPDATE_INTERVAL = 50;  // 50ms minimum between updates
    static const int SERVO_DEADBAND = 2;  // Degrees deadband to prevent jitter

    // Button press detection
    bool buttonPressed[5];

public:
    HardwareModule();
    void init();
    void update();
    
    // LED Control
    void setLED(int ledNumber, bool state);
    void setAllLEDs(bool state);
    bool getLEDState(int ledNumber);
    void toggleLEDSequence();  // New method for button-triggered sequence
    
    // Button Reading
    bool getButtonState(int buttonNumber);
    bool isButtonPressed(int buttonNumber); // Returns true only on press event
    
    // Analog Reading
    int getAnalogValue(); // Returns 0-4095
    float getAnalogVoltage(); // Returns voltage 0-3.3V
    int getAnalogPercent(); // Returns 0-100%
    
    // Servo Control
    void setServoAngle(int angle);      // Manual servo control
    int getServoAngle();                // Get current servo angle
    void updatePotentiometerServo();    // Update servo based on potentiometer
    
    // Status
    void printStatus();

private:
    // Helper methods
    int mapPotToServo(int potValue);    // Map potentiometer value to servo angle
    bool servoAngleChanged(int newAngle); // Check if servo angle change is significant
};

#endif