#ifndef HARDWARE_MODULE_H
#define HARDWARE_MODULE_H

#include <Arduino.h>

class HardwareModule {
private:
    // GPIO Pin Definitions
    static const int LED_PINS[5];
    static const int BUTTON_PINS[5];
    static const int POTENTIOMETER_PIN = 34; // ADC1_CH6
    
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
    
    // Status
    void printStatus();
};

#endif