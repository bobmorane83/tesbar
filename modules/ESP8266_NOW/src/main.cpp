#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <FS.h>
#include <ArduinoJson.h>
#include <map>
#include <vector>
extern "C" {
#include <espnow.h>
}
#include "led_manager.h"

// --- LED Configuration ---
#define LED_PIN D2  // WS2812B data pin
#define NUM_LEDS 16 // Maximum number of LEDs

LedManager leds(LED_PIN, NUM_LEDS);

// --- CAN frame message format ---
typedef struct __attribute__((packed)) {
  uint32_t id;
  uint8_t extended; // 0 = standard, 1 = extended
  uint8_t dlc;      // data length code (0..8)
  uint8_t data[8];
} can_esp_msg_t;

// --- Ring buffer ---
#define RX_QUEUE_SIZE 16
typedef struct {
  uint8_t mac[6];
  can_esp_msg_t frame;
} rx_item_t;

volatile uint8_t rx_head = 0;
volatile uint8_t rx_tail = 0;
rx_item_t rx_queue[RX_QUEUE_SIZE];

// --- Structure pour les signaux ---
typedef struct {
  uint32_t id;
  String signal_name;
  uint8_t start_bit;
  uint8_t length;
  bool little_endian;
  String active_value;
  String inactive_value;
  std::map<uint32_t, String> choices;
} signal_desc_t;

// --- Structure pour les segments ---
typedef struct {
  uint8_t start;
  uint8_t end;
  String color;
  String mode;
  uint16_t speed;
  bool reverse;
  String name;
  signal_desc_t signal;
  uint8_t segment_index;
} segment_desc_t;

std::vector<segment_desc_t> segments;

// --- Fonction pour extraire un champ de bits ---
uint32_t extract_bits(const uint8_t *data, uint8_t start_bit, uint8_t length, bool little_endian) {
  uint32_t val = 0;
  if (little_endian) {
    for (uint8_t i = 0; i < length; ++i) {
      uint8_t bit_index = start_bit + i;
      uint8_t byte = bit_index / 8;
      uint8_t bit = bit_index % 8;
      val |= ((data[byte] >> bit) & 0x1) << i;
    }
  } else {
    for (uint8_t i = 0; i < length; ++i) {
      uint8_t bit_index = start_bit + i;
      uint8_t byte = 7 - (bit_index / 8);
      uint8_t bit = 7 - (bit_index % 8);
      val |= ((data[byte] >> bit) & 0x1) << (length - 1 - i);
    }
  }
  return val;
}

// --- Web Server Configuration ---
ESP8266WebServer server(80);
const char* ssid = "ESP8266_JSON_Uploader";
const char* password = "password123";

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
void loadConfiguration() {
  if (!SPIFFS.exists("/segments.json")) {
    Serial.println("segments.json not found!");
    return;
  }

  File file = SPIFFS.open("/segments.json", "r");
  if (!file) {
    Serial.println("Failed to open segments.json");
    return;
  }

  // Lire le contenu du fichier
  String jsonContent = "";
  while (file.available()) {
    jsonContent += (char)file.read();
  }
  file.close();

  // Parser le JSON
  DynamicJsonDocument doc(2048); // Ajuster la taille si nécessaire
  DeserializationError error = deserializeJson(doc, jsonContent);
  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    return;
  }

  // Extraire num_leds si nécessaire (mais déjà défini)
  // uint8_t num_leds = doc["num_leds"];

  // Parser les segments
  JsonArray segmentsArray = doc["segments"];
  for (JsonObject segmentObj : segmentsArray) {
    segment_desc_t seg;

    // Parser le segment
    JsonObject segJson = segmentObj["segment"];
    seg.start = segJson["start"];
    seg.end = segJson["end"];
    seg.color = segJson["color"].as<String>();
    seg.mode = segJson["mode"].as<String>();
    seg.speed = segJson["speed"];
    seg.reverse = segJson["reverse"];
    seg.name = segJson["name"].as<String>();

    // Parser le signal
    JsonObject sigJson = segmentObj["signal"];
    seg.signal.id = sigJson["id"];
    seg.signal.signal_name = sigJson["signal"].as<String>();
    seg.signal.start_bit = sigJson["start"];
    seg.signal.length = sigJson["length"];
    seg.signal.little_endian = (sigJson["byte_order"] == "little_endian");
    seg.signal.active_value = sigJson["active_value"].as<String>();
    seg.signal.inactive_value = sigJson["inactive_value"].as<String>();

    // Parser les choices
    JsonObject choicesObj = sigJson["choices"];
    for (JsonPair kv : choicesObj) {
      uint32_t key = atoi(kv.key().c_str());
      String value = kv.value().as<String>();
      seg.signal.choices[key] = value;
    }

    // Créer le segment dans LedManager (assumer une méthode addSegment)
    // seg.segment_index = leds.addSegment(seg.start, seg.end, seg.mode, seg.speed, seg.reverse, seg.color);
    // Pour l'instant, utiliser addSingleLedSegment si start == end
    if (seg.start == seg.end) {
      seg.segment_index = leds.addSingleLedSegment(seg.start);
    } else {
      // Si plusieurs LEDs, assumer une méthode pour plage
      // seg.segment_index = leds.addSegment(seg.start, seg.end);
      Serial.printf("Segment with multiple LEDs not supported yet: %d-%d\n", seg.start, seg.end);
      seg.segment_index = 0xFF; // Invalide
    }

    segments.push_back(seg);
  }

  Serial.printf("Loaded %d segments\n", segments.size());
}

// --- Web Server Handlers ---
void handleRoot() {
  String html = "<html><body>";
  html += "<h1>Upload JSON Configuration</h1>";
  html += "<form action='/upload' method='post' enctype='multipart/form-data'>";
  html += "<input type='file' name='jsonFile' accept='.json'><br><br>";
  html += "<input type='submit' value='Upload'>";
  html += "</form>";
  
  // Check if segments.json exists and display it
  if (SPIFFS.exists("/segments.json")) {
    html += "<hr><h2>Fichier existant en flash :</h2>";
    File file = SPIFFS.open("/segments.json", "r");
    if (file) {
      html += "<pre>";
      while (file.available()) {
        html += (char)file.read();
      }
      html += "</pre>";
      file.close();
    } else {
      html += "<p>Erreur lors de la lecture du fichier.</p>";
    }
  }
  
  html += "</body></html>";
  server.send(200, "text/html", html);
}

void handleUpload() {
  HTTPUpload& upload = server.upload();
  if (upload.status == UPLOAD_FILE_START) {
    String filename = "/segments.json"; // Save as segments.json in SPIFFS
    SPIFFS.remove(filename); // Remove existing file
    File file = SPIFFS.open(filename, "w");
    if (!file) {
      server.send(500, "text/plain", "Failed to open file for writing");
      return;
    }
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    File file = SPIFFS.open("/segments.json", "a");
    if (file) {
      file.write(upload.buf, upload.currentSize);
      file.close();
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    server.send(200, "text/plain", "File uploaded successfully!");
  }
}

// --- Setup ---
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\nESP8266 ESP-NOW receiver starting...");

  // Initialize SPIFFS
  if (!SPIFFS.begin()) {
    Serial.println("SPIFFS initialization failed!");
    return;
  }

  // Load configuration from segments.json
  loadConfiguration();

  // Initialize LED strip
  leds.begin();
  
  // Segments are already created in loadConfiguration()

  // Setup WiFi Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP(ssid, password);
  Serial.println("WiFi AP started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  // Setup Web Server
  server.on("/", handleRoot);
  server.on("/upload", HTTP_POST, []() { server.send(200); }, handleUpload);
  server.begin();
  Serial.println("Web server started");

  // ESP-NOW setup
  WiFi.disconnect();
  delay(100);

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
    for (auto& seg : segments) {
      if (item.frame.id == seg.signal.id) {
        uint32_t raw = extract_bits(item.frame.data, seg.signal.start_bit, seg.signal.length, seg.signal.little_endian);
        String str_val = seg.signal.choices.count(raw) ? seg.signal.choices[raw] : "UNKNOWN";

        // Serial.printf("[CAN] id=0x%X signal=%s value=%s\n",
        //               item.frame.id,
        //               seg.signal.signal_name.c_str(),
        //               str_val.c_str());
        
        // Update LED segment if mapped
        if (seg.segment_index != 0xFF) {
          bool is_active = (str_val == seg.signal.active_value);
          bool is_inactive = (str_val == seg.signal.inactive_value);
          if (is_active || is_inactive) {
            leds.updateSegment(seg.segment_index, is_active);
          }
        }
      }
    }

    processed++;
    yield();
  }
  
  // Update LED animations
  leds.update();

  delay(2);
}
