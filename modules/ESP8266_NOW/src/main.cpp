#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <WS2812FX.h>
#include <map>
#include <vector>
extern "C" {
#include <espnow.h>
}
#include "helpers.h"
#include "config.h"
#include "web_handlers.h"

// --- LED Configuration ---
#define LED_PIN D2  // WS2812B data pin
#define DEFAULT_NUM_LEDS 16 // Default number of LEDs
#define MAX_NUM_LEDS 160 // Maximum safe number of LEDs

WS2812FX ws2812fx = WS2812FX(MAX_NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

// --- CAN frame message format ---
// Moved to config.h

// --- Ring buffer ---
#define RX_QUEUE_SIZE 8
typedef struct {
  uint8_t mac[6];
  can_esp_msg_t frame;
} rx_item_t;

volatile uint8_t rx_head = 0;
volatile uint8_t rx_tail = 0;
rx_item_t rx_queue[RX_QUEUE_SIZE];

// --- Structure pour les signaux ---
// Moved to config.h

// --- Structure pour les segments ---
// Moved to config.h

// Moved to config.cpp

// --- Fonctions helper pour WS2812FX ---
// Moved to helpers.h/cpp

// --- Fonction pour extraire un champ de bits ---
// Moved to helpers.h/cpp

// --- Fonction pour traiter un frame CAN ---
// Moved to config.cpp

// --- Web Server Configuration ---
ESP8266WebServer server(80);
const char* ssid = "ESP8266_JSON_Uploader";
const char* password = "password123";
const int WIFI_CHANNEL = 1; // Fix channel for AP + ESP-NOW stability

// WiFi event handlers for debugging
WiFiEventHandler onStaConn, onStaDisc;

// --- Callback de réception ESP-NOW ---
IRAM_ATTR void onDataRecv(uint8_t *mac, uint8_t *data, uint8_t len) {
  if (len != sizeof(can_esp_msg_t)) return;

  uint8_t next = (uint8_t)((rx_head + 1) % RX_QUEUE_SIZE);
  if (next == rx_tail) return; // queue pleine

  memcpy(rx_queue[rx_head].mac, mac, 6);
  memcpy(&rx_queue[rx_head].frame, data, sizeof(can_esp_msg_t));
  rx_head = next;
}

// --- Fonction pour charger la configuration depuis segments.json ---
// Moved to config.h/cpp

// --- Web Server Handlers ---
// Moved to web_handlers.h/cpp

// --- Setup ---
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\nESP8266 ESP-NOW receiver starting...");

  // Initialize LittleFS
  if (!LittleFS.begin()) {
    Serial.println("LittleFS initialization failed!");
    return;
  }

  // Initialize WS2812FX once at startup (pre-allocated for 160 LEDs)
  Serial.println("Initializing WS2812FX with 160 LEDs...");
  ws2812fx.init();
  ws2812fx.setBrightness(50); // Moderate brightness
  ws2812fx.start();
  Serial.println("WS2812FX initialized successfully");

  // Load configuration from segments.json (will only reconfigure segments)
  loadConfiguration();

  // Segments are already created in loadConfiguration()

  // Setup WiFi Access Point (fixed channel for stability with ESP-NOW)
  WiFi.mode(WIFI_AP);
  bool ap_ok = WiFi.softAP(ssid, password, WIFI_CHANNEL, false);
  Serial.printf("WiFi AP %s on channel %d\n", ap_ok ? "started" : "failed", WiFi.channel());
  Serial.print("AP IP Address: ");
  Serial.println(WiFi.softAPIP());

  // WiFi event logging
  onStaConn = WiFi.onSoftAPModeStationConnected([](const WiFiEventSoftAPModeStationConnected& evt){
    Serial.printf("[WiFi] STA connected: %02X:%02X:%02X:%02X:%02X:%02X, AID=%d\n",
      evt.mac[0], evt.mac[1], evt.mac[2], evt.mac[3], evt.mac[4], evt.mac[5], evt.aid);
  });
  onStaDisc = WiFi.onSoftAPModeStationDisconnected([](const WiFiEventSoftAPModeStationDisconnected& evt){
    Serial.printf("[WiFi] STA disconnected: %02X:%02X:%02X:%02X:%02X:%02X, AID=%d\n",
      evt.mac[0], evt.mac[1], evt.mac[2], evt.mac[3], evt.mac[4], evt.mac[5], evt.aid);
  });

  // Setup Web Server
  server.on("/", handleRoot);
  server.on("/simulate", handleSimulate);
  server.on("/upload", HTTP_POST, []() { server.send(200); }, handleUpload);
  server.begin();
  Serial.println("Web server started");

  // ESP-NOW setup (AP mode already set with fixed channel)
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  esp_now_set_self_role(ESP_NOW_ROLE_COMBO);
  esp_now_register_recv_cb(onDataRecv);
  Serial.println("ESP-NOW initialized, waiting for broadcast messages...");
}

// --- Loop ---
void loop() {
  server.handleClient(); // Handle web server requests

  const uint8_t MAX_PER_LOOP = 8;
  uint8_t processed = 0;

  while ((rx_tail != rx_head) && (processed < MAX_PER_LOOP)) {
    uint8_t idx = rx_tail;
    rx_item_t item;
    memcpy(&item, &rx_queue[idx], sizeof(item));
    rx_tail = (uint8_t)((rx_tail + 1) % RX_QUEUE_SIZE);

    // Filtrage et affichage
    processFrame(item.frame);

    processed++;
    yield();
  }
  
  // Update LED animations
  ws2812fx.service();
  yield();

  // Periodic diagnostics
  static unsigned long lastDiag = 0;
  unsigned long now = millis();
  if (now - lastDiag > 5000) {
    lastDiag = now;
    Serial.printf("[Diag] Uptime=%lus, FreeHeap=%u, AP Clients=%d, Chan=%d\n",
      now/1000, ESP.getFreeHeap(), WiFi.softAPgetStationNum(), WiFi.channel());
  }

  delay(2);
}
