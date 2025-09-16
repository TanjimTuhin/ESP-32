#include "HardwareModule.h"

// Pin definitions
const int HardwareModule::LED_PINS[5] = {2, 4, 5, 18, 19};
const int HardwareModule::BUTTON_PINS[5] = {12, 13, 14, 15, 16};

HardwareModule::HardwareModule() {
    // Initialize arrays
    for (int i = 0; i < 5; i++) {
        buttonStates[i] = false;
        lastButtonStates[i] = false;
        lastDebounceTime[i] = 0;
        buttonPressed[i] = false;
    }
    
    // Initialize analog smoothing
    analogIndex = 0;
    analogTotal = 0;
    for (int i = 0; i < ANALOG_SAMPLES; i++) {
        analogReadings[i] = 0;
    }
    
    // Initialize servo variables
    currentServoAngle = 90;
    lastPotServoAngle = 90;
    lastServoUpdate = 0;
}

void HardwareModule::init() {
    Serial.println("[HW] Initializing Hardware Module...");
    
    // Initialize LED pins
    for (int i = 0; i < 5; i++) {
        pinMode(LED_PINS[i], OUTPUT);
        digitalWrite(LED_PINS[i], LOW);
        Serial.printf("[HW] LED %d initialized on pin %d\n", i+1, LED_PINS[i]);
    }
    
    // Initialize button pins with internal pull-up
    for (int i = 0; i < 5; i++) {
        pinMode(BUTTON_PINS[i], INPUT_PULLUP);
        Serial.printf("[HW] Button %d initialized on pin %d\n", i+1, BUTTON_PINS[i]);
    }
    
    // Initialize analog pin
    pinMode(POTENTIOMETER_PIN, INPUT);
    Serial.printf("[HW] Potentiometer initialized on pin %d\n", POTENTIOMETER_PIN);
    
    // Initialize servo motor
    servoMotor.attach(SERVO_PIN);
    setServoAngle(90);
    Serial.printf("[HW] Servo motor initialized on pin %d (center position)\n", SERVO_PIN);

    // Fill initial analog readings
    for (int i = 0; i < ANALOG_SAMPLES; i++) {
        analogReadings[i] = analogRead(POTENTIOMETER_PIN);
        analogTotal += analogReadings[i];
        delay(10);
    }
    
    Serial.println("[HW] Hardware Module initialized successfully!");
}

void HardwareModule::update() {
    // Update button states with debouncing and press detection
    for (int i = 0; i < 5; i++) {
        bool reading = !digitalRead(BUTTON_PINS[i]); // Inverted because of pull-up
        
        if (reading != lastButtonStates[i]) {
            lastDebounceTime[i] = millis();
        }
        
        if ((millis() - lastDebounceTime[i]) > DEBOUNCE_DELAY) {
            if (reading != buttonStates[i]) {
                // State changed
                bool oldState = buttonStates[i];
                buttonStates[i] = reading;
                
                // Detect button press (transition from false to true)
                if (!oldState && reading) {
                    buttonPressed[i] = true;
                    Serial.printf("[HW] Button %d pressed - triggering LED sequence\n", i+1);
                }
            }
        }
        
        lastButtonStates[i] = reading;
    }
    
    // Update analog reading with smoothing
    analogTotal = analogTotal - analogReadings[analogIndex];
    analogReadings[analogIndex] = analogRead(POTENTIOMETER_PIN);
    analogTotal = analogTotal + analogReadings[analogIndex];
    analogIndex = (analogIndex + 1) % ANALOG_SAMPLES;
    
    // Update servo based on potentiometer
    updatePotentiometerServo();
}

void HardwareModule::setLED(int ledNumber, bool state) {
    if (ledNumber >= 0 && ledNumber < 5) {
        digitalWrite(LED_PINS[ledNumber], state ? HIGH : LOW);
    }
}

void HardwareModule::setAllLEDs(bool state) {
    for (int i = 0; i < 5; i++) {
        setLED(i, state);
    }
}

void HardwareModule::toggleLEDSequence() {
    Serial.println("[HW] Starting LED toggle sequence");
    
    // Turn on LEDs in sequence
    for (int i = 0; i < 5; i++) {
        setLED(i, true);
        delay(200);
    }
    
    delay(500);
    
    // Turn off LEDs in sequence
    for (int i = 0; i < 5; i++) {
        setLED(i, false);
        delay(200);
    }
    
    Serial.println("[HW] LED toggle sequence completed");
}

void HardwareModule::setServoAngle(int angle) {
    // Constrain angle to valid range (0-180 degrees)
    angle = constrain(angle, 0, 180);
    currentServoAngle = angle;
    servoMotor.write(angle);
}

int HardwareModule::getServoAngle() {
    return currentServoAngle;
}

void HardwareModule::updatePotentiometerServo() {
    // Only update servo at specified intervals to prevent jitter
    if (millis() - lastServoUpdate < SERVO_UPDATE_INTERVAL) {
        return;
    }
    
    int potValue = getAnalogValue();
    int newServoAngle = mapPotToServo(potValue);
    
    // Only update if the change is significant (deadband)
    if (servoAngleChanged(newServoAngle)) {
        setServoAngle(newServoAngle);
        lastPotServoAngle = newServoAngle;
        lastServoUpdate = millis();
        
        Serial.printf("[HW] Potentiometer servo update: %d -> %d degrees (pot: %d)\n", 
                     lastPotServoAngle, newServoAngle, potValue);
    }
}

int HardwareModule::mapPotToServo(int potValue) {
    // Map potentiometer value (0-4095) to servo angle (0-180)
    return map(potValue, 0, 4095, 0, 180);
}

bool HardwareModule::servoAngleChanged(int newAngle) {
    return abs(newAngle - lastPotServoAngle) > SERVO_DEADBAND;
}

bool HardwareModule::getLEDState(int ledNumber) {
    if (ledNumber >= 0 && ledNumber < 5) {
        return digitalRead(LED_PINS[ledNumber]);
    }
    return false;
}

bool HardwareModule::getButtonState(int buttonNumber) {
    if (buttonNumber >= 0 && buttonNumber < 5) {
        return buttonStates[buttonNumber];
    }
    return false;
}

bool HardwareModule::isButtonPressed(int buttonNumber) {
    if (buttonNumber >= 0 && buttonNumber < 5) {
        if (buttonPressed[buttonNumber]) {
            buttonPressed[buttonNumber] = false; // Reset flag
            return true;
        }
    }
    return false;
}

int HardwareModule::getAnalogValue() {
    return analogTotal / ANALOG_SAMPLES;
}

float HardwareModule::getAnalogVoltage() {
    return (getAnalogValue() * 3.3) / 4095.0;
}

int HardwareModule::getAnalogPercent() {
    return map(getAnalogValue(), 0, 4095, 0, 100);
}

void HardwareModule::printStatus() {
    Serial.println("\n=== Hardware Status ===");
    
    // LED Status
    Serial.print("LEDs: ");
    for (int i = 0; i < 5; i++) {
        Serial.printf("LED%d:%s ", i+1, getLEDState(i) ? "ON" : "OFF");
    }
    Serial.println();
    
    // Button Status
    Serial.print("Buttons: ");
    for (int i = 0; i < 5; i++) {
        Serial.printf("BTN%d:%s ", i+1, getButtonState(i) ? "PRESSED" : "RELEASED");
    }
    Serial.println();
    
    // Analog Status
    Serial.printf("Potentiometer: %d (%.2fV, %d%%) -> Servo: %d degrees\n", 
                  getAnalogValue(), getAnalogVoltage(), getAnalogPercent(), getServoAngle());
                  
    Serial.println("=====================\n");
}