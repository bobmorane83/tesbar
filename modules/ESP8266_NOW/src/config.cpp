#include "config.h"

std::vector<segment_desc_t> segments;

// --- Fonction pour charger la configuration depuis segments.json ---
void loadConfiguration() {
  if (!LittleFS.exists("/segments.json")) {
    Serial.println("segments.json not found!");
    return;
  }

  File file = LittleFS.open("/segments.json", "r");
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
  JsonDocument doc; // Utilise JsonDocument pour une gestion automatique de la mémoire
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
  for (size_t i = 0; i < segmentsArray.size(); ++i) {
    JsonObject segmentObj = segmentsArray[i];
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

    // Convertir mode et color
    seg.mode_int = getMode(seg.mode);
    seg.color_int = getColor(seg.color);

    // Créer le segment dans WS2812FX
    seg.segment_index = i; // Use i as segment index
    uint32_t black[1] = {0};
    ws2812fx.setSegment(i, seg.start, seg.end, 0, black, 0, (uint8_t)0); // Initial to static black

    segments.push_back(seg);
  }

  Serial.printf("Loaded %d segments\n", segments.size());
}

// --- Fonction pour traiter un frame CAN ---
void processFrame(can_esp_msg_t frame) {
  for (auto& seg : segments) {
    if (frame.id == seg.signal.id) {
      uint32_t raw = extract_bits(frame.data, seg.signal.start_bit, seg.signal.length, seg.signal.little_endian);
      String str_val = seg.signal.choices.count(raw) ? seg.signal.choices[raw] : "UNKNOWN";

      // Serial.printf("[CAN] id=0x%X signal=%s value=%s\n",
      //               frame.id,
      //               seg.signal.signal_name.c_str(),
      //               str_val.c_str());
      
      // Update LED segment
      if (seg.segment_index != 0xFF) {
        bool is_active = (str_val == seg.signal.active_value);
        bool is_inactive = (str_val == seg.signal.inactive_value);
        if (is_active) {
          uint32_t colors[1] = {seg.color_int};
          ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, seg.mode_int, colors, seg.speed, seg.reverse ? REVERSE : NO_OPTIONS);
        } else if (is_inactive) {
          uint32_t black[1] = {0};
          ws2812fx.setSegment(seg.segment_index, seg.start, seg.end, 0, black, 0, NO_OPTIONS);
        }
      }
    }
  }
}
