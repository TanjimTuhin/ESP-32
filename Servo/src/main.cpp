#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// WiFi credentials - Change these to your network
const char* ssid = "Spectrum Eng."; 
const char* password = "Secl@2021";

// Pin definitions
const int servoPin = 23;      // Servo connected to D23
const int potPin = 34;        // Potentiometer connected to D34 (ADC pin)

// Servo setup
Servo myServo;
int currentAngle = 90;        // Current servo angle
int previousAngle = 90;       // Previous angle for change detection
int potValue = 0;             // Raw potentiometer reading
bool manualControl = false;   // Flag for manual vs web control

// Web server on port 80
WebServer server(80);

// Function declarations
void handleRoot();
void handleSetAngle();
void handleGetCurrentAngle();
void handleGetStatus();
void readPotentiometer();

// HTML page with real-time updates
const char* htmlPage = R"(
<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>ESP32 Servo + Potentiometer Controller</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 { margin-bottom: 30px; color: #fff; }
        .angle-display {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
            padding: 15px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
        }
        .pot-info {
            font-size: 16px;
            margin: 10px 0;
            padding: 10px;
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
        }
        .slider-container {
            margin: 30px 0;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: rgba(255,255,255,0.3);
            outline: none;
            margin: 20px 0;
        }
        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            background: #4CAF50;
            cursor: pointer;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        .button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            border: none;
            color: white;
            padding: 15px 20px;
            margin: 5px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .button:active { transform: translateY(0); }
        .increment-btn {
            background: linear-gradient(45deg, #FF6B6B, #FF8E53);
            font-size: 24px; width: 60px; height: 60px; border-radius: 50%;
        }
        .decrement-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            font-size: 24px; width: 60px; height: 60px; border-radius: 50%;
        }
        .preset-buttons {
            display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin: 20px 0;
        }
        .preset-btn { background: linear-gradient(45deg, #11998e, #38ef7d); min-width: 60px; }
        .controls {
            display: flex; align-items: center; justify-content: center; gap: 20px; margin: 20px 0;
        }
        .status {
            margin: 20px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;
        }
        .control-source {
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 5px;
        }
        .web-control { background: linear-gradient(45deg, #11998e, #38ef7d); }
        .pot-control { background: linear-gradient(45deg, #FF6B6B, #FF8E53); }
    </style>
</head>
<body>
    <div class='container'>
        <h1>🎛️ Servo + Potentiometer Controller</h1>
        
        <div class='angle-display' id='angleDisplay'>90°</div>
        
        <div class='pot-info'>
            <div>Potentiometer: <span id='potValue'>2048</span> (Raw)</div>
            <div class='control-source' id='controlSource'>Web Control</div>
        </div>
        
        <div class='slider-container'>
            <label>Web Slider Control:</label>
            <input type='range' min='0' max='180' value='90' class='slider' id='angleSlider' oninput='setAngle(this.value, true)'>
            <div style='display: flex; justify-content: space-between; margin-top: 5px;'>
                <span>0°</span><span>90°</span><span>180°</span>
            </div>
        </div>
        
        <div class='controls'>
            <button class='button decrement-btn' onclick='decrementAngle()'>-</button>
            <span style='font-size: 18px; margin: 0 20px;'>Fine Control</span>
            <button class='button increment-btn' onclick='incrementAngle()'>+</button>
        </div>
        
        <div class='preset-buttons'>
            <button class='button preset-btn' onclick='setAngle(0, true)'>0°</button>
            <button class='button preset-btn' onclick='setAngle(30, true)'>30°</button>
            <button class='button preset-btn' onclick='setAngle(45, true)'>45°</button>
            <button class='button preset-btn' onclick='setAngle(90, true)'>90°</button>
            <button class='button preset-btn' onclick='setAngle(120, true)'>120°</button>
            <button class='button preset-btn' onclick='setAngle(150, true)'>150°</button>
            <button class='button preset-btn' onclick='setAngle(180, true)'>180°</button>
        </div>
        
        <div class='status' id='status'>Ready - Turn potentiometer or use web controls</div>
    </div>

    <script>
        let currentAngle = 90;
        let isWebControl = false;
        
        function updateDisplay(angle, potValue, controlSource) {
            document.getElementById('angleDisplay').textContent = angle + '°';
            document.getElementById('potValue').textContent = potValue;
            
            // Update slider only if not being dragged
            if (!isWebControl) {
                document.getElementById('angleSlider').value = angle;
            }
            
            // Update control source indicator
            const sourceElement = document.getElementById('controlSource');
            if (controlSource === 'pot') {
                sourceElement.textContent = 'Potentiometer Control';
                sourceElement.className = 'control-source pot-control';
            } else {
                sourceElement.textContent = 'Web Control';
                sourceElement.className = 'control-source web-control';
            }
            
            currentAngle = angle;
        }
        
        function setAngle(angle, fromWeb = false) {
            angle = parseInt(angle);
            if (angle < 0) angle = 0;
            if (angle > 180) angle = 180;
            
            isWebControl = fromWeb;
            
            if (fromWeb) {
                document.getElementById('status').textContent = 'Web control: Moving to ' + angle + '°...';
                
                fetch('/setAngle?angle=' + angle + '&source=web')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('status').textContent = 'Web control: Position ' + angle + '°';
                    })
                    .catch(error => {
                        document.getElementById('status').textContent = 'Error: ' + error;
                    });
            }
            
            setTimeout(() => { isWebControl = false; }, 100);
        }
        
        function incrementAngle() {
            let newAngle = currentAngle + 1;
            if (newAngle <= 180) setAngle(newAngle, true);
        }
        
        function decrementAngle() {
            let newAngle = currentAngle - 1;
            if (newAngle >= 0) setAngle(newAngle, true);
        }
        
        // Continuously update from ESP32
        function updateStatus() {
            fetch('/getStatus')
                .then(response => response.json())
                .then(data => {
                    updateDisplay(data.angle, data.potValue, data.source);
                    if (data.source === 'pot') {
                        document.getElementById('status').textContent = 
                            'Potentiometer control: ' + data.angle + '° (Raw: ' + data.potValue + ')';
                    }
                })
                .catch(error => console.log('Update error:', error));
        }
        
        // Update every 200ms for real-time feedback
        setInterval(updateStatus, 200);
        
        // Initial update
        updateStatus();
    </script>
</body>
</html>
)";

void setup() {
    Serial.begin(115200);
    Serial.println("ESP32 Servo + Potentiometer Controller Starting...");
    
    // Initialize servo
    myServo.attach(servoPin);
    myServo.write(currentAngle);
    delay(500);
    
    // Initialize potentiometer pin (ADC)
    pinMode(potPin, INPUT);
    
    Serial.println("Hardware initialized:");
    Serial.println("- Servo on pin D23");
    Serial.println("- Potentiometer on pin D34");
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.println("Open this IP in your browser to control the servo");
    
    // Web server routes
    server.on("/", handleRoot);
    server.on("/setAngle", handleSetAngle);
    server.on("/getCurrentAngle", handleGetCurrentAngle);
    server.on("/getStatus", handleGetStatus);
    
    server.begin();
    Serial.println("Web server started");
    Serial.println("Both potentiometer and web interface are active!");
}

void loop() {
    server.handleClient();
    readPotentiometer();
    delay(10);
}

// Read potentiometer and update servo
void readPotentiometer() {
    static unsigned long lastPotRead = 0;
    static int lastPotAngle = -1;
    
    // Read potentiometer every 50ms
    if (millis() - lastPotRead > 50) {
        lastPotRead = millis();
        
        // Read potentiometer (0-4095 on ESP32)
        potValue = analogRead(potPin);
        
        // Convert to servo angle (0-180)
        int potAngle = map(potValue, 0, 4095, 0, 180);
        potAngle = constrain(potAngle, 0, 180);
        
        // Only update if angle changed significantly (reduce jitter)
        if (abs(potAngle - lastPotAngle) > 1) {
            lastPotAngle = potAngle;
            currentAngle = potAngle;
            myServo.write(currentAngle);
            manualControl = true;
            
            Serial.print("Potentiometer control - Angle: ");
            Serial.print(currentAngle);
            Serial.print("° (Raw: ");
            Serial.print(potValue);
            Serial.println(")");
        }
    }
}

// Serve the main HTML page
void handleRoot() {
    server.send(200, "text/html", htmlPage);
}

// Handle angle setting from web interface
void handleSetAngle() {
    if (server.hasArg("angle")) {
        int angle = server.arg("angle").toInt();
        String source = server.hasArg("source") ? server.arg("source") : "web";
        
        if (angle >= 0 && angle <= 180) {
            currentAngle = angle;
            myServo.write(angle);
            manualControl = (source != "web");
            
            Serial.print("Web control - Servo moved to: ");
            Serial.print(angle);
            Serial.println("°");
            
            server.send(200, "text/plain", "OK");
        } else {
            server.send(400, "text/plain", "Invalid angle");
        }
    } else {
        server.send(400, "text/plain", "Missing angle parameter");
    }
}

// Return current angle
void handleGetCurrentAngle() {
    server.send(200, "text/plain", String(currentAngle));
}

// Return complete status (angle, pot value, control source)
void handleGetStatus() {
    String json = "{";
    json += "\"angle\":" + String(currentAngle) + ",";
    json += "\"potValue\":" + String(potValue) + ",";
    json += "\"source\":\"" + String(manualControl ? "pot" : "web") + "\"";
    json += "}";
    
    server.send(200, "application/json", json);
    
    // Reset manual control flag after a delay
    static unsigned long lastWebControl = 0;
    if (!manualControl) {
        lastWebControl = millis();
    }
    if (manualControl && (millis() - lastWebControl > 2000)) {
        manualControl = false;
    }
}