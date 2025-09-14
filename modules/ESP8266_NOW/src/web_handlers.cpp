#include "web_handlers.h"
#include <cstring>
#include <cstdarg>

// --- Web Server Handlers ---
void handleRoot() {
  // Buffer HTML optimisé pour économiser RAM
  const size_t HTML_BUFFER_SIZE = 4096;
  static char html_buffer[HTML_BUFFER_SIZE];
  size_t html_pos = 0;

  // Fonction helper pour ajouter du texte au buffer
  auto addToBuffer = [&](const char* text) {
    size_t len = strlen(text);
    if (html_pos + len < HTML_BUFFER_SIZE) {
      strcpy(&html_buffer[html_pos], text);
      html_pos += len;
    }
  };

  // Fonction helper pour ajouter du texte formaté
  auto addFormatted = [&](const char* format, ...) {
    va_list args;
    va_start(args, format);
    size_t remaining = HTML_BUFFER_SIZE - html_pos;
    if (remaining > 0) {
      int written = vsnprintf(&html_buffer[html_pos], remaining, format, args);
      if (written > 0 && (size_t)written < remaining) {
        html_pos += written;
      }
    }
    va_end(args);
  };

  // Début HTML
  addToBuffer("<html><body>");
  addToBuffer("<h1>Upload JSON Configuration</h1>");
  addToBuffer("<form action='/upload' method='post' enctype='multipart/form-data'>");
  addToBuffer("<input type='file' name='jsonFile' accept='.json'><br><br>");
  addToBuffer("<input type='submit' value='Upload'>");
  addToBuffer("</form>");
  
  // Quick Wi-Fi status
  addToBuffer("<hr><h2>Wi-Fi</h2>");
  addFormatted("<p>AP SSID: %s</p>", WiFi.softAPSSID().c_str());
  addFormatted("<p>Channel: %d | Clients: %d</p>", WiFi.channel(), WiFi.softAPgetStationNum());
  addFormatted("<p>IP: %s</p>", WiFi.softAPIP().toString().c_str());

  // Add simulation buttons
  if (!segments.empty()) {
    addToBuffer("<hr><h2>Simulation des signaux</h2>");
    for (size_t i = 0; i < segments.size(); ++i) {
      auto& seg = segments[i];
      addFormatted("<h3>Segment %d: %s</h3>", (int)i, seg.signal.signal_name);
      addFormatted("<form action='/simulate' method='get' style='display:inline;'>");
      addFormatted("<input type='hidden' name='seg' value='%d'>", (int)i);
      addToBuffer("<input type='hidden' name='state' value='active'>");
      addFormatted("<button type='submit'>Activer (%s)</button>", seg.signal.active_value);
      addToBuffer("</form> ");
      addFormatted("<form action='/simulate' method='get' style='display:inline;'>");
      addFormatted("<input type='hidden' name='seg' value='%d'>", (int)i);
      addToBuffer("<input type='hidden' name='state' value='inactive'>");
      addFormatted("<button type='submit'>Désactiver (%s)</button>", seg.signal.inactive_value);
      addToBuffer("</form><br><br>");
    }
  } else {
    addToBuffer("<hr><p>Aucun segment chargé. Uploadez le fichier segments.json via le formulaire ci-dessus.</p>");
  }
  
  // Check if segments.json exists and display encoded configuration
  if (LittleFS.exists("/segments.json")) {
    // Limiter la taille du dump pour ne pas dépasser le buffer
    size_t before = html_pos;
    displayEncodedConfiguration(html_buffer, HTML_BUFFER_SIZE, html_pos);
    if (html_pos >= HTML_BUFFER_SIZE - 128) {
      // Si on approche la limite, tronquer et avertir
      const char* warn = "<p><b>Affichage tronqué (trop de segments)</b></p>";
      size_t warn_len = strlen(warn);
      if (html_pos + warn_len < HTML_BUFFER_SIZE) {
        strcpy(&html_buffer[html_pos], warn);
        html_pos += warn_len;
      }
      // Terminer la chaîne proprement
      html_buffer[HTML_BUFFER_SIZE-1] = '\0';
    }
  }
  
  addToBuffer("</body></html>");
  html_buffer[html_pos] = '\0'; // Terminer la chaîne
  
  server.send(200, "text/html", html_buffer);
}

void handleUpload() {
  HTTPUpload& upload = server.upload();
  if (upload.status == UPLOAD_FILE_START) {
    String filename = "/segments.json"; // Save as segments.json in LittleFS
    LittleFS.remove(filename); // Remove existing file
    File file = LittleFS.open(filename, "w");
    if (!file) {
      server.send(500, "text/plain", "Failed to open file for writing");
      return;
    }
  file.close();
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    File file = LittleFS.open("/segments.json", "a");
    if (file) {
      file.write(upload.buf, upload.currentSize);
      file.close();
    }
  } else if (upload.status == UPLOAD_FILE_END) {
  // Invalider le cache encodé et recharger la configuration depuis le JSON
  Serial.println("Upload terminé: invalidation du cache /config.bin et rechargement JSON");
  LittleFS.remove("/config.bin");
    loadConfiguration();
    // Rediriger vers la page principale
    server.sendHeader("Location", "/");
    server.send(302);
  }
}

// --- Handler pour simuler un signal ---
void handleSimulate() {
  if (server.hasArg("seg") && server.hasArg("state")) {
    int segIndex = server.arg("seg").toInt();
    String state = server.arg("state");
    if (segIndex >= 0 && segIndex < (int)segments.size()) {
      auto& seg = segments[segIndex];
      
      // Vérifier l'état demandé
      if (state != "active" && state != "inactive") {
        server.send(400, "text/plain", "Invalid state");
        return;
      }

      // Find the raw value for target_value
      uint32_t raw = 0;
      bool found = false;
      const char* target_str = (state == "active") ? seg.signal.active_value : seg.signal.inactive_value;
      for (uint8_t j = 0; j < seg.signal.choices_count; j++) {
        if (strcmp(seg.signal.choices[j].value, target_str) == 0) {
          raw = seg.signal.choices[j].key;
          found = true;
          break;
        }
      }
      if (!found) {
        server.send(400, "text/plain", "Value not found in choices");
        return;
      }

      // Create fake frame
      can_esp_msg_t fake_frame;
      fake_frame.id = seg.signal.id;
      fake_frame.extended = 0;
      fake_frame.dlc = 8;
      memset(fake_frame.data, 0, 8);

      // Set the bits
      if (seg.signal.little_endian) {
        for (uint8_t i = 0; i < seg.signal.length; ++i) {
          uint8_t bit_index = seg.signal.start_bit + i;
          uint8_t byte = bit_index / 8;
          uint8_t bit = bit_index % 8;
          if (raw & (1 << i)) {
            fake_frame.data[byte] |= (1 << bit);
          }
        }
      } else {
        for (uint8_t i = 0; i < seg.signal.length; ++i) {
          uint8_t bit_index = seg.signal.start_bit + i;
          uint8_t byte = 7 - (bit_index / 8);
          uint8_t bit = 7 - (bit_index % 8);
          if (raw & (1 << (seg.signal.length - 1 - i))) {
            fake_frame.data[byte] |= (1 << bit);
          }
        }
      }

      // Process the fake frame
      processFrame(fake_frame);
      server.sendHeader("Location", "/");
      server.send(302);
    } else {
      server.send(400, "text/plain", "Invalid segment index");
    }
  } else {
    server.send(400, "text/plain", "Missing parameters");
  }
}
