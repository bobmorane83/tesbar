#include "helpers.h"

// --- Fonctions helper pour WS2812FX ---
uint8_t getMode(String modeStr) {
  if (modeStr == "STATIC") return 0;
  if (modeStr == "BLINK") return 1;
  if (modeStr == "BREATHE") return 2;
  if (modeStr == "COLOR_WIPE") return 3;
  if (modeStr == "COLOR_WIPE_INV") return 4;
  if (modeStr == "COLOR_WIPE_REV") return 5;
  if (modeStr == "COLOR_WIPE_REV_INV") return 6;
  if (modeStr == "FADE") return 7;
  if (modeStr == "THEATER_CHASE") return 8;
  if (modeStr == "THEATER_CHASE_RAINBOW") return 9;
  if (modeStr == "RAINBOW") return 10;
  if (modeStr == "RAINBOW_CYCLE") return 11;
  if (modeStr == "SCAN") return 12;
  if (modeStr == "DUAL_SCAN") return 13;
  if (modeStr == "RUNNING_LIGHTS") return 17;
  if (modeStr == "TWINKLE") return 18;
  if (modeStr == "TWINKLE_RANDOM") return 19;
  if (modeStr == "TWINKLE_FADE") return 20;
  if (modeStr == "TWINKLE_FADE_RANDOM") return 21;
  if (modeStr == "SPARKLE") return 22;
  if (modeStr == "FLASH_SPARKLE") return 23;
  if (modeStr == "HYPER_SPARKLE") return 24;
  if (modeStr == "STROBE") return 25;
  if (modeStr == "STROBE_RAINBOW") return 26;
  if (modeStr == "MULTI_STROBE") return 27;
  if (modeStr == "BLINK_RAINBOW") return 28;
  if (modeStr == "CHASE_WHITE") return 29;
  if (modeStr == "CHASE_COLOR") return 30;
  if (modeStr == "CHASE_RANDOM") return 31;
  if (modeStr == "CHASE_RAINBOW") return 32;
  if (modeStr == "CHASE_FLASH") return 33;
  if (modeStr == "CHASE_FLASH_RANDOM") return 34;
  if (modeStr == "CHASE_RAINBOW_WHITE") return 35;
  if (modeStr == "CHASE_BLACKOUT") return 36;
  if (modeStr == "CHASE_BLACKOUT_RAINBOW") return 37;
  if (modeStr == "COLOR_SWEEP_RANDOM") return 38;
  if (modeStr == "RUNNING_COLOR") return 39;
  if (modeStr == "RUNNING_RED_BLUE") return 40;
  if (modeStr == "RUNNING_RANDOM") return 41;
  if (modeStr == "LARSON_SCANNER") return 42;
  if (modeStr == "COMET") return 43;
  if (modeStr == "FIREWORKS") return 44;
  if (modeStr == "FIREWORKS_RANDOM") return 45;
  if (modeStr == "MERRY_CHRISTMAS") return 46;
  if (modeStr == "FIRE_FLICKER") return 47;
  if (modeStr == "FIRE_FLICKER_SOFT") return 48;
  if (modeStr == "FIRE_FLICKER_INTENSE") return 49;
  if (modeStr == "CIRCUS_COMBUSTUS") return 50;
  if (modeStr == "HALLOWEEN") return 51;
  if (modeStr == "BICOLOR_CHASE") return 52;
  if (modeStr == "TRICOLOR_CHASE") return 53;
  if (modeStr == "ICU") return 54;
  return 0; // Default STATIC
}

uint32_t getColor(String colorStr) {
  if (colorStr.startsWith("#") && colorStr.length() == 7) {
    return strtol(colorStr.c_str() + 1, NULL, 16);
  }
  return 0; // Black
}

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
