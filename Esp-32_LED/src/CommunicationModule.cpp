#include "CommunicationModule.h"

CommunicationModule::CommunicationModule(HardwareModule* hw) 
    : server(SERVER_PORT), hardware(hw) {
    activeClients = 0;
    lastUpdate = 0;
    lastStatusPrint = 0;
    
    // Initialize client array
    for (int i = 0; i < MAX_CLIENTS; i++) {
        clients[i].authenticated = false;
        clients[i].active = false;
        clients[i].lastHeartbeat = 0;
        clients[i].clientId = "";
    }
}

void CommunicationModule::init() {
    Serial.println("[COMM] Initializing Communication Module...");
    
    // Setup WiFi Access Point
    Serial.printf("[COMM] Setting up WiFi Access Point: %s\n", ssid);
    WiFi.mode(WIFI_AP);
    WiFi.softAP(ssid, password);
    
    IPAddress IP = WiFi.softAPIP();
    Serial.printf("[COMM] Access Point IP: %s\n", IP.toString().c_str());
    
    // Start TCP server
    server.begin();
    Serial.printf("[COMM] TCP Server started on port %d\n", SERVER_PORT);
    Serial.printf("[COMM] Authentication password: %s\n", auth_password);
    
    Serial.println("[COMM] Communication Module initialized successfully!");
    Serial.println("[COMM] Clients can connect to:");
    Serial.printf("[COMM]   WiFi: %s (Password: %s)\n", ssid, password);
    Serial.printf("[COMM]   Server: %s:%d\n", IP.toString().c_str(), SERVER_PORT);
}

void CommunicationModule::update() {
    handleNewClients();
    handleClientMessages();
    
    // Send periodic updates
    if (millis() - lastUpdate > UPDATE_INTERVAL) {
        sendDataToClients();
        removeInactiveClients();
        lastUpdate = millis();
    }
    
    // Print status periodically
    if (millis() - lastStatusPrint > 10000) { // Every 10 seconds
        printServerStatus();
        lastStatusPrint = millis();
    }
}

void CommunicationModule::handleNewClients() {
    WiFiClient newClient = server.available();
    if (newClient) {
        int slot = findFreeClientSlot();
        if (slot != -1) {
            clients[slot].client = newClient;
            clients[slot].active = true;
            clients[slot].authenticated = false;
            clients[slot].lastHeartbeat = millis();
            clients[slot].clientId = "Client_" + String(slot + 1);
            activeClients++;
            
            Serial.printf("[COMM] New client connected: %s (Slot %d)\n", 
                         clients[slot].clientId.c_str(), slot);
            
            sendAuthChallenge(slot);
        } else {
            // Server full
            newClient.println("{\"status\":\"error\",\"message\":\"Server full\"}");
            newClient.stop();
            Serial.println("[COMM] Connection rejected: Server full");
        }
    }
}

void CommunicationModule::handleClientMessages() {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active && clients[i].client.connected()) {
            if (clients[i].client.available()) {
                String message = clients[i].client.readStringUntil('\n');
                message.trim();
                
                if (message.length() > 0) {
                    clients[i].lastHeartbeat = millis();
                    processClientMessage(i, message);
                }
            }
        }
    }
}

void CommunicationModule::sendDataToClients() {
    String statusJson = createStatusJson();
    
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active && clients[i].authenticated && clients[i].client.connected()) {
            clients[i].client.println(statusJson);
        }
    }
}

void CommunicationModule::removeInactiveClients() {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active) {
            if (!clients[i].client.connected() || 
                (millis() - clients[i].lastHeartbeat > HEARTBEAT_TIMEOUT)) {
                
                Serial.printf("[COMM] Removing inactive client: %s\n", 
                             clients[i].clientId.c_str());
                closeClient(i);
            }
        }
    }
}

void CommunicationModule::processClientMessage(int clientIndex, String message) {
    Serial.printf("[COMM] Message from %s: %s\n", 
                 clients[clientIndex].clientId.c_str(), message.c_str());
    
    // Parse JSON
    DeserializationError error = deserializeJson(jsonDoc, message);
    if (error) {
        sendResponse(clientIndex, createResponseJson("error", "Invalid JSON"));
        return;
    }
    
    String command = jsonDoc["command"];
    
    // Handle authentication
    if (!clients[clientIndex].authenticated) {
        if (command == "auth") {
            String pwd = jsonDoc["password"];
            if (authenticateClient(clientIndex, pwd)) {
                clients[clientIndex].authenticated = true;
                sendResponse(clientIndex, createResponseJson("success", "Authenticated"));
                Serial.printf("[COMM] Client %s authenticated\n", 
                             clients[clientIndex].clientId.c_str());
            } else {
                sendResponse(clientIndex, createResponseJson("error", "Invalid password"));
                Serial.printf("[COMM] Authentication failed for %s\n", 
                             clients[clientIndex].clientId.c_str());
            }
        } else {
            sendResponse(clientIndex, createResponseJson("error", "Authentication required"));
        }
        return;
    }
    
    // Handle authenticated commands
    if (command == "set_led") {
        int ledNum = jsonDoc["led"];
        bool state = jsonDoc["state"];
        
        if (ledNum >= 1 && ledNum <= 5) {
            hardware->setLED(ledNum - 1, state);
            sendResponse(clientIndex, createResponseJson("success", 
                        "LED " + String(ledNum) + " set to " + (state ? "ON" : "OFF")));
        } else {
            sendResponse(clientIndex, createResponseJson("error", "Invalid LED number (1-5)"));
        }
    }
    else if (command == "set_all_leds") {
        bool state = jsonDoc["state"];
        hardware->setAllLEDs(state);
        sendResponse(clientIndex, createResponseJson("success", 
                    "All LEDs set to " + String(state ? "ON" : "OFF")));
    }
    else if (command == "get_status") {
        sendResponse(clientIndex, createStatusJson());
    }
    else if (command == "ping") {
        sendResponse(clientIndex, createResponseJson("success", "pong"));
    }
    else {
        sendResponse(clientIndex, createResponseJson("error", "Unknown command"));
    }
}

void CommunicationModule::sendResponse(int clientIndex, const String& response) {
    if (clients[clientIndex].active && clients[clientIndex].client.connected()) {
        clients[clientIndex].client.println(response);
    }
}

void CommunicationModule::sendAuthChallenge(int clientIndex) {
    String challenge = createResponseJson("auth_required", 
                      "Send authentication: {\"command\":\"auth\",\"password\":\"your_password\"}");
    sendResponse(clientIndex, challenge);
}

bool CommunicationModule::authenticateClient(int clientIndex, const String& password) {
    return password.equals(auth_password);
}

String CommunicationModule::createStatusJson() {
    jsonDoc.clear();
    
    jsonDoc["type"] = "status";
    jsonDoc["timestamp"] = millis();
    
    // LED states
    JsonArray leds = jsonDoc.createNestedArray("leds");
    for (int i = 0; i < 5; i++) {
        JsonObject led = leds.createNestedObject();
        led["id"] = i + 1;
        led["state"] = hardware->getLEDState(i);
    }
    
    // Button states
    JsonArray buttons = jsonDoc.createNestedArray("buttons");
    for (int i = 0; i < 5; i++) {
        JsonObject button = buttons.createNestedObject();
        button["id"] = i + 1;
        button["pressed"] = hardware->getButtonState(i);
    }
    
    // Analog data
    JsonObject analog = jsonDoc.createNestedObject("potentiometer");
    analog["raw"] = hardware->getAnalogValue();
    analog["voltage"] = hardware->getAnalogVoltage();
    analog["percent"] = hardware->getAnalogPercent();
    
    serializeJson(jsonDoc, jsonBuffer);
    return String(jsonBuffer);
}

String CommunicationModule::createResponseJson(const String& status, const String& message) {
    jsonDoc.clear();
    jsonDoc["status"] = status;
    jsonDoc["message"] = message;
    jsonDoc["timestamp"] = millis();
    
    serializeJson(jsonDoc, jsonBuffer);
    return String(jsonBuffer);
}

void CommunicationModule::printServerStatus() {
    Serial.println("\n=== Server Status ===");
    Serial.printf("Active Clients: %d/%d\n", activeClients, MAX_CLIENTS);
    Serial.printf("WiFi Clients: %d\n", WiFi.softAPgetStationNum());
    
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (clients[i].active) {
            Serial.printf("Slot %d: %s - %s - Last seen: %lus ago\n", 
                         i, 
                         clients[i].clientId.c_str(),
                         clients[i].authenticated ? "AUTH" : "PENDING",
                         (millis() - clients[i].lastHeartbeat) / 1000);
        }
    }
    Serial.println("====================\n");
}

int CommunicationModule::findFreeClientSlot() {
    for (int i = 0; i < MAX_CLIENTS; i++) {
        if (!clients[i].active) {
            return i;
        }
    }
    return -1;
}

void CommunicationModule::closeClient(int clientIndex) {
    if (clients[clientIndex].active) {
        clients[clientIndex].client.stop();
        clients[clientIndex].active = false;
        clients[clientIndex].authenticated = false;
        clients[clientIndex].clientId = "";
        activeClients--;
    }
}