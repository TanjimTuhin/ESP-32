#ifndef COMMUNICATION_MODULE_H
#define COMMUNICATION_MODULE_H

#include <WiFi.h>
#include <WiFiServer.h>
#include <ArduinoJson.h>
#include "HardwareModule.h"

struct ClientInfo {
    WiFiClient client;           // TCP client connection
    bool authenticated;          // Authentication status
    unsigned long lastHeartbeat; // Last activity timestamp
    String clientId;            // Unique client identifier
    bool active;                // Connection status
};

class CommunicationModule {
private:
    // Network Configuration
    const char* ssid = "SECL RnD LAB";
    const char* password = "SECL@2024";
    const char* auth_password = "IoTDevice2024";
    
    // Server Configuration
    WiFiServer server;
    static const int SERVER_PORT = 8080;
    static const int MAX_CLIENTS = 5;
    static const unsigned long HEARTBEAT_TIMEOUT = 30000; // 30 seconds
    static const unsigned long UPDATE_INTERVAL = 1000;    // 1 second
    
    // Client Management
    ClientInfo clients[MAX_CLIENTS];
    int activeClients;
    
    // Hardware Reference
    HardwareModule* hardware;
    
    // Timing
    unsigned long lastUpdate;
    unsigned long lastStatusPrint;
    
    // JSON Documents
    StaticJsonDocument<1024> jsonDoc;
    char jsonBuffer[1024];
    
public:
    CommunicationModule(HardwareModule* hw);
    void init();
    void update();
    
private:
    // Client management functions
    void handleNewClients();
    void handleClientMessages();
    void sendDataToClients();
    void removeInactiveClients();

    // Message processing functions
    void processClientMessage(int clientIndex, String message);
    void sendResponse(int clientIndex, const String& response);
    
    // Authentication functions
    void sendAuthChallenge(int clientIndex);
    bool authenticateClient(int clientIndex, const String& password);
    void sendHeartbeat(int clientIndex);
    
    // JSON helper functions
    String createStatusJson();
    String createResponseJson(const String& status, const String& message);
    void printServerStatus();
    int findFreeClientSlot();
    void closeClient(int clientIndex);
};

#endif