#include "web_handlers.h"
#include <cstring>

// --- Web Server Handlers ---
void handleRoot() {
  String html = "<html><body>";
  html += "<h1>Upload JSON Configuration</h1>";
  html += "<form action='/upload' method='post' enctype='multipart/form-data'>";
  html += "<input type='file' name='jsonFile' accept='.json'><br><br>";
  html += "<input type='submit' value='Upload'>";
  html += "</form>";
  
  // Check if segments.json exists and display it
  if (LittleFS.exists("/segments.json")) {
    html += "<hr><h2>Fichier existant en flash :</h2>";
    File file = LittleFS.open("/segments.json", "r");
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
  
  // Add simulation buttons
  if (!segments.empty()) {
    html += "<hr><h2>Simulation des signaux</h2>";
    for (size_t i = 0; i < segments.size(); ++i) {
      auto& seg = segments[i];
      html += "<h3>Segment " + String(i) + ": " + seg.signal.signal_name + "</h3>";
      html += "<form action='/simulate' method='get' style='display:inline;'>";
      html += "<input type='hidden' name='seg' value='" + String(i) + "'>";
      html += "<input type='hidden' name='state' value='active'>";
      html += "<button type='submit'>Activer (" + seg.signal.active_value + ")</button>";
      html += "</form> ";
      html += "<form action='/simulate' method='get' style='display:inline;'>";
      html += "<input type='hidden' name='seg' value='" + String(i) + "'>";
      html += "<input type='hidden' name='state' value='inactive'>";
      html += "<button type='submit'>Désactiver (" + seg.signal.inactive_value + ")</button>";
      html += "</form><br><br>";
    }
  } else {
    html += "<hr><p>Aucun segment chargé. Uploadez le fichier segments.json via le formulaire ci-dessus.</p>";
  }
  
  html += "</body></html>";
  server.send(200, "text/html", html);
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
  } else if (upload.status == UPLOAD_FILE_WRITE) {
    File file = LittleFS.open("/segments.json", "a");
    if (file) {
      file.write(upload.buf, upload.currentSize);
      file.close();
    }
  } else if (upload.status == UPLOAD_FILE_END) {
    server.send(200, "text/plain", "File uploaded successfully!");
  }
}

// --- Handler pour simuler un signal ---
void handleSimulate() {
  if (server.hasArg("seg") && server.hasArg("state")) {
    int segIndex = server.arg("seg").toInt();
    String state = server.arg("state");
    if (segIndex >= 0 && segIndex < (int)segments.size()) {
      auto& seg = segments[segIndex];
      String target_value;
      if (state == "active") {
        target_value = seg.signal.active_value;
      } else if (state == "inactive") {
        target_value = seg.signal.inactive_value;
      } else {
        server.send(400, "text/plain", "Invalid state");
        return;
      }

      // Find the raw value for target_value
      uint32_t raw = 0;
      bool found = false;
      for (auto& pair : seg.signal.choices) {
        if (pair.second == target_value) {
          raw = pair.first;
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
