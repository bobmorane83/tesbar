#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <LittleFS.h>
#include <ArduinoJson.h>
#include <WS2812FX.h>
#include <map>
#include <vector>
#include "helpers.h"

extern WS2812FX ws2812fx;

// --- CAN frame message format ---
typedef struct __attribute__((packed)) {
  uint32_t id;
  uint8_t extended; // 0 = standard, 1 = extended
  uint8_t dlc;      // data length code (0..8)
  uint8_t data[8];
} can_esp_msg_t;

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
  uint8_t mode_int;
  uint32_t color_int;
} segment_desc_t;

extern std::vector<segment_desc_t> segments;

void loadConfiguration();
void processFrame(can_esp_msg_t frame);

#endif
