#ifndef HARDWARE_MODULE_H
#define HARDWARE_MODULE_H

#include <Arduino.h>
#include <ESP32Servo.h>  // Add ESP32Servo library

class HardwareModule {
private:
    // GPIO Pin Definitions
    static const int LED_PINS[5];
    static const int BUTTON_PINS[5];
    static const int POTENTIOMETER_PIN = 34; // ADC1_CH6
    static const int SERVO_PIN = 23;         // Add servo pin definition

    // Button debouncing
    bool buttonStates[5];
    bool lastButtonStates[5];
    unsigned long lastDebounceTime[5];
    static const unsigned long DEBOUNCE_DELAY = 50;
    
    // Analog reading smoothing
    static const int ANALOG_SAMPLES = 10;
    int analogReadings[ANALOG_SAMPLES];
    int analogIndex;
    long analogTotal;
    
    // Servo object
    Servo servoMotor;  // Add servo object

public:
    HardwareModule();
    void init();
    void update();
    
    // LED Control
    void setLED(int ledNumber, bool state);
    void setAllLEDs(bool state);
    bool getLEDState(int ledNumber);
    
    // Button Reading
    bool getButtonState(int buttonNumber);
    bool isButtonPressed(int buttonNumber); // Returns true only on press event
    
    // Analog Reading
    int getAnalogValue(); // Returns 0-4095
    float getAnalogVoltage(); // Returns voltage 0-3.3V
    int getAnalogPercent(); // Returns 0-100%
    
    // Servo Control - Add these methods
    void setServoAngle(int angle);      // Set servo angle (0-180 degrees)
    int getServoAngle();                // Get current servo angle
    
    // Status
    void printStatus();
};

#endif