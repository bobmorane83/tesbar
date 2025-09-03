#include <Arduino.h>
#include <ESP8266WiFi.h>
extern "C" {
#include <espnow.h>
}
#include "led_manager.h"

// --- LED Configuration ---
#define LED_PIN D2  // WS2812B data pin
#define NUM_LEDS 16 // Maximum number of LEDs

LedManager leds(LED_PIN, NUM_LEDS);
uint8_t signal_to_segment[16] = {0xFF}; // Map signal index to LED segment

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

// --- Description structure correspondant au JSON ---
typedef struct {
  uint32_t message_id;
  const char* message_name;
  const char* signal_name;
  uint8_t start_bit;
  uint8_t length;
  bool little_endian; // true si little_endian
  const char* values[4]; // max 4 pour cet exemple
} can_signal_desc_t;

// --- Liste des signaux basés sur ton JSON ---
can_signal_desc_t can_desc[] = {
  {
    1013,
    "ID3F5VCFRONT_lighting",
    "VCFRONT_indicatorLeftRequest",
    0,
    2,
    true,
    { "TURN_SIGNAL_OFF", "TURN_SIGNAL_ACTIVE_LOW", "TURN_SIGNAL_ACTIVE_HIGH" }
  },
  {
    1013,
    "ID3F5VCFRONT_lighting",
    "VCFRONT_indicatorRightRequest",
    2,
    2,
    true,
    { "TURN_SIGNAL_OFF", "TURN_SIGNAL_ACTIVE_LOW", "TURN_SIGNAL_ACTIVE_HIGH" }
  }
};

const size_t NUM_SIGNALS = sizeof(can_desc)/sizeof(can_desc[0]);

// --- Callback de réception ESP-NOW ---
IRAM_ATTR void onDataRecv(uint8_t *mac, uint8_t *data, uint8_t len) {
  if (len != sizeof(can_esp_msg_t)) return;

  uint8_t next = (uint8_t)((rx_head + 1) % RX_QUEUE_SIZE);
  if (next == rx_tail) return; // queue pleine

  memcpy(rx_queue[rx_head].mac, mac, 6);
  memcpy(&rx_queue[rx_head].frame, data, sizeof(can_esp_msg_t));
  rx_head = next;
}

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

// --- Setup ---
void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\nESP8266 ESP-NOW receiver starting...");

  // Initialize LED strip
  leds.begin();
  
  // Create one segment per signal, each with 1 LED in static mode
  for (size_t i = 0; i < NUM_SIGNALS; i++) {
    signal_to_segment[i] = leds.addSingleLedSegment(i);
    if (signal_to_segment[i] == 0xFF) {
      Serial.printf("Failed to create segment for signal %u\n", i);
    }
  }

  WiFi.mode(WIFI_STA);
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
  const uint8_t MAX_PER_LOOP = 8;
  uint8_t processed = 0;

  while ((rx_tail != rx_head) && (processed < MAX_PER_LOOP)) {
    uint8_t idx = rx_tail;
    rx_item_t item;
    memcpy(&item, &rx_queue[idx], sizeof(item));
    rx_tail = (uint8_t)((rx_tail + 1) % RX_QUEUE_SIZE);

    // Filtrage et affichage
    for (size_t s = 0; s < NUM_SIGNALS; ++s) {
      if (item.frame.id == can_desc[s].message_id) {
        uint32_t raw = extract_bits(item.frame.data, can_desc[s].start_bit, can_desc[s].length, can_desc[s].little_endian);
        const char* str_val = "UNKNOWN";
        if (raw < 4) str_val = can_desc[s].values[raw];

        // Serial.printf("[CAN] id=0x%X signal=%s value=%s\n",
        //               item.frame.id,
        //               can_desc[s].signal_name,
        //               str_val);
        
        // Update LED segment if mapped
        if (signal_to_segment[s] != 0xFF) {
          bool is_on = (strcmp(str_val, "TURN_SIGNAL_ACTIVE_HIGH") == 0) ||
                      (strcmp(str_val, "TURN_SIGNAL_ACTIVE_LOW") == 0);
          leds.updateSegment(signal_to_segment[s], is_on);
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
