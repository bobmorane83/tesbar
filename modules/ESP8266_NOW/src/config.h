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

// --- Constantes ---
#define ENCODED_SEGMENTS_SIZE 50

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
  const char* signal_name;
  uint8_t start_bit;
  uint8_t length;
  bool little_endian;
  const char* active_value;
  const char* inactive_value;
  // Tableau fixe pour les choices (max 8 paires)
  struct {
    uint32_t key;
    const char* value;
  } choices[8];
  uint8_t choices_count;
} signal_desc_t;

// --- Structure pour les segments ---
typedef struct {
  uint8_t start;
  uint8_t end;
  const char* color;
  const char* mode;
  uint16_t speed;
  bool reverse;
  const char* name;
  signal_desc_t signal;
  uint8_t segment_index;
  uint8_t mode_int;
  uint32_t color_int;
} segment_desc_t;

// --- Structure encodée pour stockage compact ---
typedef struct __attribute__((packed)) {
  uint8_t start;
  uint8_t end;
  uint16_t speed;
  uint8_t flags; // bit 0: reverse, bits 1-7: mode_int
  uint32_t color_int;
  // Signal data
  uint32_t signal_id;
  uint8_t signal_start_bit;
  uint8_t signal_length;
  uint8_t signal_flags; // bit 0: little_endian, bits 1-7: choices_count
  // Indices dans le buffer de chaînes (uint16_t pour chaque chaîne)
  uint16_t name_idx;
  uint16_t color_str_idx;
  uint16_t mode_str_idx;
  uint16_t signal_name_idx;
  uint16_t active_value_idx;
  uint16_t inactive_value_idx;
  // Choices (max 8)
  struct __attribute__((packed)) {
    uint32_t key;
    uint16_t value_idx;
  } choices[8];
} encoded_segment_t;

// --- Structure pour le stockage des données encodées en flash ---
#define CONFIG_MAGIC 0xC0FFEEAA  // Magic number pour valider les données
#define CONFIG_VERSION 2         // Version du format de données (2 = ajoute table de chaînes persistante)

// Taille de la table de chaînes persistante encodée
#ifndef ENCODED_STRINGS_SIZE
#define ENCODED_STRINGS_SIZE 3072
#endif

typedef struct __attribute__((packed)) {
  uint32_t magic;        // Magic number pour validation
  uint16_t version;      // Version du format
  uint16_t num_leds;     // Nombre de LEDs
  uint16_t num_segments; // Nombre de segments
  uint32_t checksum;     // Checksum des données
  // Table de chaînes persistante (offsets 16-bit utilisés dans encoded_segment_t)
  uint16_t strings_used;
  char strings[ENCODED_STRINGS_SIZE];
  // Suivi des données encodées
  encoded_segment_t segments[ENCODED_SEGMENTS_SIZE];
} encoded_config_t;

extern encoded_config_t encoded_config;

// Fonctions d'encodage/décodage
void encodeSegments();
void displayEncodedConfiguration(char* buffer, size_t buffer_size, size_t& pos);

// Fonctions principales
void loadConfiguration();
void processFrame(can_esp_msg_t frame);

extern std::vector<segment_desc_t> segments;

#endif
