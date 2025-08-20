#include <Arduino.h>
#include <WiFi.h>

const char* ssid     = "SECL RnD LAB";   //  Wi-Fi SSID
const char* password = "SECL@2024";      //  Wi-Fi password

WiFiServer server(3333);   // TCP server on port 3333
#define LED 2              // onboard LED (GPIO2 on ESP32 boards)

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📶 SSID: ");
    Serial.println(WiFi.SSID());
    Serial.print("💻 ESP32 IP address: ");
    Serial.println(WiFi.localIP());
    server.begin();
  } else {
    Serial.println("\n❌ WiFi connection failed, retrying in 5s...");
    delay(5000);
    connectToWiFi(); // try again
  }
}

void setup() {
  pinMode(LED, OUTPUT);
  Serial.begin(115200);
  delay(1000);

  connectToWiFi();
}

void loop() {
  // Reconnect Wi-Fi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }

  WiFiClient client = server.available();
  if (!client) return;

  String cmd = client.readStringUntil('\n');
  cmd.trim();

  if (cmd == "ON") {
    digitalWrite(LED, HIGH);
    client.println("LED is ON");
    Serial.println("LED turned ON via client");
  }
  else if (cmd == "OFF") {
    digitalWrite(LED, LOW);
    client.println("LED is OFF");
    Serial.println("LED turned OFF via client");
  }
  else {
    client.println("Unknown command");
    Serial.println("Received unknown command: " + cmd);
  }
}
