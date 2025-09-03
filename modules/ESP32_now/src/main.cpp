#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include "can_port.h"

// Broadcast address
static uint8_t broadcastAddress[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};

// ESP-NOW send callback (optional)
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Debug if needed
}

// CAN port instance
CANPort canPort;

// Message format forwarded over ESP-NOW
typedef struct __attribute__((packed)) {
  uint32_t id;
  uint8_t extended;
  uint8_t dlc;
  uint8_t data[8];
} can_esp_msg_t;

void setup() {
  Serial.begin(115200);
  delay(100);

  // Initialize ESP-NOW
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(50);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
  }
  esp_now_register_send_cb(OnDataSent);

  esp_now_peer_info_t peerInfo;
  memset(&peerInfo, 0, sizeof(peerInfo));
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
#if defined(ESP32)
  peerInfo.channel = 0;
  peerInfo.ifidx = WIFI_IF_STA;
#endif
  peerInfo.encrypt = false;
  esp_err_t pr = esp_now_add_peer(&peerInfo);
  if (pr != ESP_OK) Serial.println("Failed to add broadcast peer (may already exist)");

  // Initialize CAN port: CS=25, INT=26, bitrate=500kbps, oscillator=16MHz
  if (!canPort.begin(25, 26, CAN_500KBPS, MCP_8MHZ)) {
    Serial.println("CAN port init failed");
  } else {
    Serial.println("CAN port initialized (500kbps, 16MHz)");
  }

  Serial.println("Ready: forwarding CAN -> ESP-NOW");
}

void loop() {
  // Poll CAN port continuously and forward frames immediately via ESP-NOW
  while (canPort.available()) {
    uint32_t id;
    uint8_t dlc;
    uint8_t buf[8];
    bool extended = false;
    if (canPort.read(id, dlc, buf, extended)) {
      can_esp_msg_t m;
      m.id = id;
      m.extended = extended ? 1 : 0;
      m.dlc = dlc;
      memset(m.data, 0, sizeof(m.data));
      memcpy(m.data, buf, dlc);

      esp_err_t res = esp_now_send(broadcastAddress, (uint8_t *)&m, sizeof(m));
      if (res != ESP_OK) {
        Serial.print("esp_now_send error: "); Serial.println(res);
      }
    }
  }

  // No delay here: loop runs continuously, forwarding frames immediately
}
