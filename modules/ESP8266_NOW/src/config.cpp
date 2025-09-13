#include "config.h"

// Buffer global pour stocker les chaînes de caractères (optimisation RAM)
#define STRING_BUFFER_SIZE 3072
static char string_buffer[STRING_BUFFER_SIZE];
static size_t string_buffer_used = 0;

// Buffer pour les segments encodés
#define ENCODED_SEGMENTS_SIZE 50
static encoded_segment_t encoded_segments[ENCODED_SEGMENTS_SIZE];
static uint8_t encoded_segments_count = 0;

// Limite maximale de LEDs (doit correspondre à main.cpp)
#define MAX_NUM_LEDS 160

// Structure globale pour le stockage en flash
encoded_config_t encoded_config;

std::vector<segment_desc_t> segments;

// Fonction helper pour copier une chaîne dans le buffer global et retourner l'index
uint16_t copyStringGetIndex(const char* str) {
  if (!str) return 0xFFFF; // Index invalide

  // Chercher si la chaîne existe déjà
  for (uint16_t i = 0; i < string_buffer_used; ) {
    size_t len = strlen(&string_buffer[i]);
    if (strcmp(&string_buffer[i], str) == 0) {
      return i; // Retourner l'index existant
    }
    i += len + 1; // Passer à la chaîne suivante
  }

  // Ajouter la nouvelle chaîne
  size_t len = strlen(str);
  if (string_buffer_used + len + 1 >= STRING_BUFFER_SIZE) {
    Serial.println("String buffer overflow!");
    return 0xFFFF;
  }

  uint16_t index = string_buffer_used;
  strcpy(&string_buffer[string_buffer_used], str);
  string_buffer_used += len + 1;

  return index;
}

// Fonction helper pour récupérer une chaîne depuis son index
const char* getStringFromIndex(uint16_t index) {
  if (index >= string_buffer_used) return "INVALID";
  return &string_buffer[index];
}

// Fonction pour calculer un checksum simple des données
uint32_t calculateChecksum(const uint8_t* data, size_t size) {
  uint32_t checksum = 0;
  for (size_t i = 0; i < size; i++) {
    checksum = ((checksum << 5) + checksum) + data[i]; // Simple hash
  }
  return checksum;
}

// Fonction pour sauvegarder la configuration encodée en flash
bool saveEncodedConfig() {
  if (!LittleFS.begin()) {
    Serial.println("LittleFS mount failed for save");
    return false;
  }

  // Préparer la structure de sauvegarde
  encoded_config.magic = CONFIG_MAGIC;
  encoded_config.version = CONFIG_VERSION;
  // Conserver le nombre de LEDs actuel si connu
  if (encoded_config.num_leds == 0) {
    // Tenter d'inférer un nombre de LEDs depuis les segments présents
    uint16_t max_end = 0;
    for (uint8_t i = 0; i < encoded_segments_count; i++) {
      if (encoded_segments[i].end > max_end) max_end = encoded_segments[i].end;
    }
    encoded_config.num_leds = (max_end > 0 && max_end <= MAX_NUM_LEDS) ? max_end : MAX_NUM_LEDS;
  }
  encoded_config.num_segments = encoded_segments_count;

  // Copier la table de chaînes encodée depuis le buffer courant
  encoded_config.strings_used = (uint16_t)min((size_t)UINT16_MAX, string_buffer_used);
  memset(encoded_config.strings, 0, ENCODED_STRINGS_SIZE);
  size_t copy_len = min((size_t)ENCODED_STRINGS_SIZE, (size_t)encoded_config.strings_used);
  if (copy_len > 0) {
    memcpy(encoded_config.strings, string_buffer, copy_len);
  }

  // Copier les segments encodés
  memcpy(encoded_config.segments, encoded_segments, sizeof(encoded_segment_t) * encoded_segments_count);

  // Calculer le checksum (strings_used + strings[] + segments[])
  uint32_t cs = 0;
  cs = calculateChecksum((const uint8_t*)&encoded_config.strings_used, sizeof(encoded_config.strings_used));
  cs = calculateChecksum((const uint8_t*)encoded_config.strings, ENCODED_STRINGS_SIZE) + cs;
  cs = calculateChecksum((const uint8_t*)encoded_config.segments, sizeof(encoded_segment_t) * encoded_segments_count) + cs;
  encoded_config.checksum = cs;

  // Sauvegarder en flash
  File file = LittleFS.open("/config.bin", "w");
  if (!file) {
    Serial.println("Failed to create config.bin");
    return false;
  }

  size_t written = file.write((uint8_t*)&encoded_config, sizeof(encoded_config_t));
  file.close();

  if (written != sizeof(encoded_config_t)) {
    Serial.println("Failed to write complete config");
    return false;
  }

  Serial.printf("Configuration saved (%d segments, checksum: 0x%08X)\n", encoded_segments_count, encoded_config.checksum);
  return true;
}

// Fonction pour charger la configuration encodée depuis flash
bool loadEncodedConfig() {
  if (!LittleFS.begin()) {
    Serial.println("LittleFS mount failed for load");
    return false;
  }

  File file = LittleFS.open("/config.bin", "r");
  if (!file) {
    Serial.println("No saved configuration found");
    return false;
  }

  size_t fileSize = file.size();
  if (fileSize != sizeof(encoded_config_t)) {
    Serial.printf("Invalid config file size: %d (expected: %d)\n", fileSize, sizeof(encoded_config_t));
    file.close();
    return false;
  }

  // Charger les données
  size_t read = file.read((uint8_t*)&encoded_config, sizeof(encoded_config_t));
  file.close();

  if (read != sizeof(encoded_config_t)) {
    Serial.println("Failed to read complete config");
    return false;
  }

  // Valider le magic number
  if (encoded_config.magic != CONFIG_MAGIC) {
    Serial.printf("Invalid magic number: 0x%08X (expected: 0x%08X)\n", encoded_config.magic, CONFIG_MAGIC);
    return false;
  }

  // Valider la version
  if (encoded_config.version != CONFIG_VERSION) {
    Serial.printf("Version mismatch: %d (expected: %d)\n", encoded_config.version, CONFIG_VERSION);
    return false;
  }

  // Valider le checksum (strings_used + strings[] + segments[])
  uint32_t calculated_checksum = 0;
  calculated_checksum = calculateChecksum((const uint8_t*)&encoded_config.strings_used, sizeof(encoded_config.strings_used));
  calculated_checksum = calculateChecksum((const uint8_t*)encoded_config.strings, ENCODED_STRINGS_SIZE) + calculated_checksum;
  calculated_checksum = calculateChecksum((const uint8_t*)encoded_config.segments, sizeof(encoded_segment_t) * encoded_config.num_segments) + calculated_checksum;
  if (calculated_checksum != encoded_config.checksum) {
    Serial.printf("Checksum mismatch: 0x%08X (calculated: 0x%08X)\n", encoded_config.checksum, calculated_checksum);
    return false;
  }

  // Copier les données validées
  encoded_segments_count = encoded_config.num_segments;
  memcpy(encoded_segments, encoded_config.segments, sizeof(encoded_segment_t) * encoded_segments_count);

  // Reconstituer la table de chaînes en mémoire
  if (encoded_config.strings_used > 0 && encoded_config.strings_used <= ENCODED_STRINGS_SIZE) {
    memset(string_buffer, 0, STRING_BUFFER_SIZE);
    size_t load_len = min((size_t)STRING_BUFFER_SIZE, (size_t)encoded_config.strings_used);
    memcpy(string_buffer, encoded_config.strings, load_len);
    string_buffer_used = load_len;
  } else {
    string_buffer_used = 0;
  }

  Serial.printf("Configuration loaded (%d segments, checksum: 0x%08X)\n", encoded_segments_count, encoded_config.checksum);
  return true;
}

// Prototypes des fonctions
void reconstructSegmentsFromEncoded();
void loadConfigurationFromJSON();

// Fonction principale pour charger la configuration depuis le fichier JSON
void loadConfiguration() {
  // Reset du buffer de chaînes
  string_buffer_used = 0;

  // Nettoyer les anciens segments avant de charger les nouveaux
  segments.clear();

  // Nettoyer tous les segments WS2812FX existants
  ws2812fx.resetSegments();

  if (!LittleFS.begin()) {
    Serial.println("LittleFS initialization failed!");
    return;
  }

  // Essayer de charger la configuration encodée validée d'abord
  if (loadEncodedConfig()) {
    Serial.println("Using cached encoded configuration");
    // Reconstruire les segments depuis les données encodées
    reconstructSegmentsFromEncoded();
    return;
  }

  Serial.println("No valid cached config, loading from JSON...");
  // Si pas de config validée, charger depuis JSON
  loadConfigurationFromJSON();
}
void reconstructSegmentsFromEncoded() {
  // Ne pas réinitialiser le buffer de chaînes ici (il est chargé depuis encoded_config)
  segments.clear();

  // Utiliser le nombre de LEDs depuis la config sauvegardée
  uint8_t num_leds = encoded_config.num_leds;
  if (num_leds == 0) num_leds = 16; // Valeur par défaut

  // Vérifier que le nombre de LEDs ne dépasse pas la limite pré-allouée
  if (num_leds > MAX_NUM_LEDS) {
    Serial.printf("Warning: LED count %d exceeds maximum %d, using maximum\n", num_leds, MAX_NUM_LEDS);
    num_leds = MAX_NUM_LEDS;
  }

  Serial.printf("Reconstructing configuration with %d LEDs (using pre-allocated instance)\n", num_leds);

  // WS2812FX is already initialized at startup - just reset segments
  Serial.println("Resetting WS2812FX segments for cached configuration...");
  ws2812fx.resetSegments();
  yield();

  // Reconstruire les segments depuis les données encodées
  for (uint8_t i = 0; i < encoded_segments_count; i++) {
    const encoded_segment_t& enc = encoded_segments[i];
    segment_desc_t seg;

    // Reconstruire les données de base
    seg.start = enc.start;
    seg.end = enc.end;
    seg.speed = enc.speed;
    seg.reverse = (enc.flags & 1);
    seg.mode_int = (enc.flags >> 1) & 0x7F;
    seg.color_int = enc.color_int;

    // Reconstruire les chaînes depuis les indices
    seg.name = getStringFromIndex(enc.name_idx);
    seg.color = getStringFromIndex(enc.color_str_idx);
    seg.mode = getStringFromIndex(enc.mode_str_idx);

    // Reconstruire les données du signal
    seg.signal.id = enc.signal_id;
    seg.signal.start_bit = enc.signal_start_bit;
    seg.signal.length = enc.signal_length;
    seg.signal.little_endian = (enc.signal_flags & 1);
    seg.signal.choices_count = (enc.signal_flags >> 1) & 0x7F;

    seg.signal.signal_name = getStringFromIndex(enc.signal_name_idx);
    seg.signal.active_value = getStringFromIndex(enc.active_value_idx);
    seg.signal.inactive_value = getStringFromIndex(enc.inactive_value_idx);

    // Reconstruire les choices
    for (uint8_t j = 0; j < seg.signal.choices_count && j < 8; j++) {
      seg.signal.choices[j].key = enc.choices[j].key;
      seg.signal.choices[j].value = getStringFromIndex(enc.choices[j].value_idx);
    }

    // Créer le segment WS2812FX
    seg.segment_index = ws2812fx.getNumSegments();
    uint32_t black[1] = {0};
    ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, 0, black, 0, NO_OPTIONS);

  segments.push_back(seg);

  if ((i & 0x3) == 0) yield();
  }

  Serial.printf("Reconstructed %d segments from cached configuration\n", segments.size());
}

// Fonction pour traiter un message CAN et mettre à jour les LEDs
void processFrame(can_esp_msg_t frame) {
  uint16_t idx = 0;
  for (auto& seg : segments) {
    if (seg.signal.id == frame.id) {
      // Extraire la valeur du signal selon le format
      uint32_t raw = extract_bits(frame.data, seg.signal.start_bit, seg.signal.length, seg.signal.little_endian);

      // Convertir en valeur string selon les choices
      const char* str_val = "UNKNOWN";
      for (uint8_t j = 0; j < seg.signal.choices_count; j++) {
        if (seg.signal.choices[j].key == raw) {
          str_val = seg.signal.choices[j].value;
          break;
        }
      }

      // Serial.printf("[CAN] id=0x%X signal=%s value=%s\n",
      //               frame.id,
      //               seg.signal.signal_name,
      //               str_val);

      // Update LED segment
      if (seg.segment_index != 0xFF) {
        bool is_active = (strcmp(str_val, seg.signal.active_value) == 0);
        bool is_inactive = (strcmp(str_val, seg.signal.inactive_value) == 0);
        if (is_active) {
          uint32_t colors[1] = {seg.color_int};
          ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, seg.mode_int, colors, seg.speed, seg.reverse ? REVERSE : NO_OPTIONS);
        } else if (is_inactive) {
          uint32_t black[1] = {0};
          ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, 0, black, 0, NO_OPTIONS);
        }
      }
    }

  if (((idx++) & 0x7) == 0) yield();
  }
}

// Fonction pour charger la configuration depuis JSON (lors du premier chargement)
void loadConfigurationFromJSON() {
  // Open the uploaded JSON file from LittleFS (consistent absolute path)
  File file = LittleFS.open("/segments.json", "r");
  if (!file) {
    Serial.println("Failed to open segments.json");
    return;
  }

  size_t fileSize = file.size();
  if (fileSize == 0) {
    Serial.println("Empty JSON file");
    file.close();
    return;
  }

  // Augmenter la taille du buffer pour supporter des fichiers JSON plus gros
  const size_t MAX_JSON_SIZE = 8192; // 8KB pour des configurations complexes
  if (fileSize > MAX_JSON_SIZE) {
    Serial.printf("JSON file too large: %d bytes (max: %d)\n", fileSize, MAX_JSON_SIZE);
    file.close();
    return;
  }

  // Lire le JSON dans un buffer alloué sur le tas (évite un gros buffer sur la pile)
  size_t bufSize = fileSize + 1;
  char* jsonBuffer = (char*)malloc(bufSize);
  if (!jsonBuffer) {
    Serial.println("Out of memory allocating JSON buffer");
    file.close();
    return;
  }
  file.readBytes(jsonBuffer, fileSize);
  jsonBuffer[fileSize] = '\0';
  file.close();

  // Parser le JSON
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, jsonBuffer, fileSize);
  free(jsonBuffer);
  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    return;
  }

  // Extraire num_leds et réinitialiser WS2812FX si nécessaire
  // Read as unsigned int first to avoid unintended truncation before clamping
  unsigned int leds_requested = doc["num_leds"] | 16; // Default 16 if not specified
  uint8_t num_leds = (leds_requested > 255) ? 255 : (uint8_t)leds_requested;

  // Vérifier que le nombre de LEDs ne dépasse pas la limite pré-allouée
  if (num_leds > MAX_NUM_LEDS) {
    Serial.printf("Warning: LED count %d exceeds maximum %d, using maximum\n", num_leds, MAX_NUM_LEDS);
    num_leds = MAX_NUM_LEDS;
  }

  Serial.printf("Configuring LED strip with %d LEDs (using pre-allocated instance)\n", num_leds);

  // Pas besoin de recréer WS2812FX - on utilise l'instance globale déjà initialisée
  // Juste s'assurer qu'elle est dans un état propre
  Serial.println("Resetting WS2812FX segments...");
  ws2812fx.resetSegments();
  yield();

  Serial.println("WS2812FX configuration updated successfully");

  // Mémoriser le nombre de LEDs pour les prochains redémarrages (reconstruction encodée)
  encoded_config.num_leds = num_leds;

  // Parser les segments
  // Validate presence and type of 'segments' array
  if (!doc["segments"].is<JsonArray>()) {
    Serial.println("JSON error: 'segments' array missing or invalid");
    return;
  }
  JsonArray segmentsArray = doc["segments"];

  // Première passe : stocker tous les indices dans le buffer de chaînes
  struct seg_indices_t {
    segment_desc_t seg;
    uint16_t color_idx, mode_idx, name_idx;
    uint16_t signal_name_idx, active_value_idx, inactive_value_idx;
    uint16_t choices_idx[8];
  };
  std::vector<seg_indices_t> segs_temp;
  for (size_t i = 0; i < segmentsArray.size(); ++i) {
    JsonObject segmentObj = segmentsArray[i];
    seg_indices_t temp;
    JsonObject segJson = segmentObj["segment"];
    temp.seg.start = segJson["start"];
    temp.seg.end = segJson["end"];
    temp.color_idx = copyStringGetIndex(segJson["color"]);
    temp.mode_idx = copyStringGetIndex(segJson["mode"]);
    temp.seg.speed = segJson["speed"];
    temp.seg.reverse = segJson["reverse"];
    temp.name_idx = copyStringGetIndex(segJson["name"]);

    JsonObject sigJson = segmentObj["signal"];
    temp.seg.signal.id = sigJson["id"];
    temp.signal_name_idx = copyStringGetIndex(sigJson["signal"]);
    temp.seg.signal.start_bit = sigJson["start"];
    temp.seg.signal.length = sigJson["length"];
    // Safer comparison for byte_order string
    {
      const char* bo = sigJson["byte_order"].as<const char*>();
      temp.seg.signal.little_endian = (bo && strcmp(bo, "little_endian") == 0);
    }
    temp.active_value_idx = copyStringGetIndex(sigJson["active_value"]);
    temp.inactive_value_idx = copyStringGetIndex(sigJson["inactive_value"]);

    JsonObject choicesObj = sigJson["choices"];
    temp.seg.signal.choices_count = 0;
    for (JsonPair kv : choicesObj) {
      if (temp.seg.signal.choices_count >= 8) break;
      uint32_t key = atoi(kv.key().c_str());
      temp.seg.signal.choices[temp.seg.signal.choices_count].key = key;
      temp.choices_idx[temp.seg.signal.choices_count] = copyStringGetIndex(kv.value().as<const char*>());
      temp.seg.signal.choices_count++;
    }

    temp.seg.segment_index = 0xFF;
    segs_temp.push_back(temp);
    if ((i & 0x3) == 0) yield();
  }

  // Deuxième passe : assigner les pointeurs depuis les indices
  for (size_t i = 0; i < segs_temp.size(); ++i) {
    seg_indices_t& temp = segs_temp[i];
    temp.seg.color = getStringFromIndex(temp.color_idx);
    temp.seg.mode = getStringFromIndex(temp.mode_idx);
    temp.seg.name = getStringFromIndex(temp.name_idx);
    temp.seg.signal.signal_name = getStringFromIndex(temp.signal_name_idx);
    temp.seg.signal.active_value = getStringFromIndex(temp.active_value_idx);
    temp.seg.signal.inactive_value = getStringFromIndex(temp.inactive_value_idx);
    for (uint8_t j = 0; j < temp.seg.signal.choices_count; ++j) {
      temp.seg.signal.choices[j].value = getStringFromIndex(temp.choices_idx[j]);
    }
    temp.seg.color_int = getColor(temp.seg.color);
    temp.seg.mode_int = getMode(temp.seg.mode);
    segments.push_back(temp.seg);
    if ((i & 0x3) == 0) yield();
  }

  // Encoder les segments pour stockage compact
  encodeSegments();

  // Sauvegarder la configuration encodée validée
  if (saveEncodedConfig()) {
    Serial.println("Configuration cached successfully");
  }

  // Initialiser les segments WS2812FX
  for (size_t i = 0; i < segments.size(); ++i) {
    segment_desc_t& seg = segments[i];
    if (seg.segment_index == 0xFF) {
      seg.segment_index = ws2812fx.getNumSegments();
      uint32_t black[1] = {0};
      ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, 0, black, 0, NO_OPTIONS);
    }

    if ((i & 0x3) == 0) yield();
  }

  Serial.printf("Loaded %d segments from JSON configuration\n", segments.size());
}

// Fonction pour encoder les segments en format compact pour stockage
void encodeSegments() {
  encoded_segments_count = 0;

  for (size_t i = 0; i < segments.size() && encoded_segments_count < ENCODED_SEGMENTS_SIZE; ++i) {
    const segment_desc_t& seg = segments[i];
    encoded_segment_t& enc = encoded_segments[encoded_segments_count];

    // Encoder les données de base
    enc.start = seg.start;
    enc.end = seg.end;
    enc.speed = seg.speed;
    enc.flags = (seg.reverse ? 1 : 0) | ((seg.mode_int & 0x7F) << 1);
    enc.color_int = seg.color_int;

    // Encoder les données du signal
    enc.signal_id = seg.signal.id;
    enc.signal_start_bit = seg.signal.start_bit;
    enc.signal_length = seg.signal.length;
    enc.signal_flags = (seg.signal.little_endian ? 1 : 0) | ((seg.signal.choices_count & 0x7F) << 1);

    // Encoder les indices de chaînes
    enc.name_idx = copyStringGetIndex(seg.name);
    enc.color_str_idx = copyStringGetIndex(seg.color);
    enc.mode_str_idx = copyStringGetIndex(seg.mode);
    enc.signal_name_idx = copyStringGetIndex(seg.signal.signal_name);
    enc.active_value_idx = copyStringGetIndex(seg.signal.active_value);
    enc.inactive_value_idx = copyStringGetIndex(seg.signal.inactive_value);

    // Encoder les choices
    for (uint8_t j = 0; j < seg.signal.choices_count && j < 8; ++j) {
      enc.choices[j].key = seg.signal.choices[j].key;
      enc.choices[j].value_idx = copyStringGetIndex(seg.signal.choices[j].value);
    }

    encoded_segments_count++;
  }

  Serial.printf("Encoded %d segments for storage\n", encoded_segments_count);
}

// Fonction pour afficher la configuration encodée (pour debug/web)
void displayEncodedConfiguration(char* buffer, size_t buffer_size, size_t& pos) {
  pos += snprintf(buffer + pos, buffer_size - pos, "=== Encoded Configuration ===\n");
  pos += snprintf(buffer + pos, buffer_size - pos, "Segments: %d\n", encoded_segments_count);
  pos += snprintf(buffer + pos, buffer_size - pos, "String buffer used: %d/%d bytes\n\n", string_buffer_used, STRING_BUFFER_SIZE);

  for (uint8_t i = 0; i < encoded_segments_count && pos < buffer_size - 200; ++i) {
    const encoded_segment_t& enc = encoded_segments[i];

    pos += snprintf(buffer + pos, buffer_size - pos, "Segment %d:\n", i);
    pos += snprintf(buffer + pos, buffer_size - pos, "  Range: %d-%d\n", enc.start, enc.end);
    pos += snprintf(buffer + pos, buffer_size - pos, "  Color: %s (0x%06X)\n", getStringFromIndex(enc.color_str_idx), enc.color_int);
    pos += snprintf(buffer + pos, buffer_size - pos, "  Mode: %s (%d)\n", getStringFromIndex(enc.mode_str_idx), (enc.flags >> 1) & 0x7F);
    pos += snprintf(buffer + pos, buffer_size - pos, "  Speed: %d, Reverse: %s\n", enc.speed, (enc.flags & 1) ? "yes" : "no");
    pos += snprintf(buffer + pos, buffer_size - pos, "  Name: %s\n", getStringFromIndex(enc.name_idx));

    pos += snprintf(buffer + pos, buffer_size - pos, "  Signal: %s (ID: 0x%X)\n", getStringFromIndex(enc.signal_name_idx), enc.signal_id);
    pos += snprintf(buffer + pos, buffer_size - pos, "    Bit range: %d-%d (%d bits)\n", enc.signal_start_bit, enc.signal_start_bit + enc.signal_length - 1, enc.signal_length);
    pos += snprintf(buffer + pos, buffer_size - pos, "    Endianness: %s\n", (enc.signal_flags & 1) ? "little" : "big");
    pos += snprintf(buffer + pos, buffer_size - pos, "    Active: %s, Inactive: %s\n", getStringFromIndex(enc.active_value_idx), getStringFromIndex(enc.inactive_value_idx));

    uint8_t choices_count = (enc.signal_flags >> 1) & 0x7F;
    if (choices_count > 0) {
      pos += snprintf(buffer + pos, buffer_size - pos, "    Choices:\n");
      for (uint8_t j = 0; j < choices_count && j < 8; ++j) {
        pos += snprintf(buffer + pos, buffer_size - pos, "      %d: %s\n", enc.choices[j].key, getStringFromIndex(enc.choices[j].value_idx));
      }
    }
    pos += snprintf(buffer + pos, buffer_size - pos, "\n");
  }
}
