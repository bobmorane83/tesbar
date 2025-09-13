#include "helpers.h"

// --- Fonctions helper pour WS2812FX ---
uint8_t getMode(String modeStr) {
  if (modeStr == "STATIC") return FX_MODE_STATIC;
  if (modeStr == "BLINK") return FX_MODE_BLINK;
  if (modeStr == "BREATHE") return FX_MODE_BREATH;
  if (modeStr == "COLOR_WIPE") return FX_MODE_COLOR_WIPE;
  if (modeStr == "COLOR_WIPE_INV") return FX_MODE_COLOR_WIPE_INV;
  if (modeStr == "COLOR_WIPE_REV") return FX_MODE_COLOR_WIPE_REV;
  if (modeStr == "COLOR_WIPE_REV_INV") return FX_MODE_COLOR_WIPE_REV_INV;
  if (modeStr == "COLOR_WIPE_RANDOM") return FX_MODE_COLOR_WIPE_RANDOM;
  if (modeStr == "RANDOM_COLOR") return FX_MODE_RANDOM_COLOR;
  if (modeStr == "SINGLE_DYNAMIC") return FX_MODE_SINGLE_DYNAMIC;
  if (modeStr == "MULTI_DYNAMIC") return FX_MODE_MULTI_DYNAMIC;
  if (modeStr == "RAINBOW") return FX_MODE_RAINBOW;
  if (modeStr == "RAINBOW_CYCLE") return FX_MODE_RAINBOW_CYCLE;
  if (modeStr == "SCAN") return FX_MODE_SCAN;
  if (modeStr == "DUAL_SCAN") return FX_MODE_DUAL_SCAN;
  if (modeStr == "FADE") return FX_MODE_FADE;
  if (modeStr == "THEATER_CHASE") return FX_MODE_THEATER_CHASE;
  if (modeStr == "THEATER_CHASE_RAINBOW") return FX_MODE_THEATER_CHASE_RAINBOW;
  if (modeStr == "RUNNING_LIGHTS") return FX_MODE_RUNNING_LIGHTS;
  if (modeStr == "TWINKLE") return FX_MODE_TWINKLE;
  if (modeStr == "TWINKLE_RANDOM") return FX_MODE_TWINKLE_RANDOM;
  if (modeStr == "TWINKLE_FADE") return FX_MODE_TWINKLE_FADE;
  if (modeStr == "TWINKLE_FADE_RANDOM") return FX_MODE_TWINKLE_FADE_RANDOM;
  if (modeStr == "SPARKLE") return FX_MODE_SPARKLE;
  if (modeStr == "FLASH_SPARKLE") return FX_MODE_FLASH_SPARKLE;
  if (modeStr == "HYPER_SPARKLE") return FX_MODE_HYPER_SPARKLE;
  if (modeStr == "STROBE") return FX_MODE_STROBE;
  if (modeStr == "STROBE_RAINBOW") return FX_MODE_STROBE_RAINBOW;
  if (modeStr == "MULTI_STROBE") return FX_MODE_MULTI_STROBE;
  if (modeStr == "BLINK_RAINBOW") return FX_MODE_BLINK_RAINBOW;
  if (modeStr == "CHASE_WHITE") return FX_MODE_CHASE_WHITE;
  if (modeStr == "CHASE_COLOR") return FX_MODE_CHASE_COLOR;
  if (modeStr == "CHASE_RANDOM") return FX_MODE_CHASE_RANDOM;
  if (modeStr == "CHASE_RAINBOW") return FX_MODE_CHASE_RAINBOW;
  if (modeStr == "CHASE_FLASH") return FX_MODE_CHASE_FLASH;
  if (modeStr == "CHASE_FLASH_RANDOM") return FX_MODE_CHASE_FLASH_RANDOM;
  if (modeStr == "CHASE_RAINBOW_WHITE") return FX_MODE_CHASE_RAINBOW_WHITE;
  if (modeStr == "CHASE_BLACKOUT") return FX_MODE_CHASE_BLACKOUT;
  if (modeStr == "CHASE_BLACKOUT_RAINBOW") return FX_MODE_CHASE_BLACKOUT_RAINBOW;
  if (modeStr == "COLOR_SWEEP_RANDOM") return FX_MODE_COLOR_SWEEP_RANDOM;
  if (modeStr == "RUNNING_COLOR") return FX_MODE_RUNNING_COLOR;
  if (modeStr == "RUNNING_RED_BLUE") return FX_MODE_RUNNING_RED_BLUE;
  if (modeStr == "RUNNING_RANDOM") return FX_MODE_RUNNING_RANDOM;
  if (modeStr == "LARSON_SCANNER") return FX_MODE_LARSON_SCANNER;
  if (modeStr == "COMET") return FX_MODE_COMET;
  if (modeStr == "FIREWORKS") return FX_MODE_FIREWORKS;
  if (modeStr == "FIREWORKS_RANDOM") return FX_MODE_FIREWORKS_RANDOM;
  if (modeStr == "MERRY_CHRISTMAS") return FX_MODE_MERRY_CHRISTMAS;
  if (modeStr == "FIRE_FLICKER") return FX_MODE_FIRE_FLICKER;
  if (modeStr == "FIRE_FLICKER_SOFT") return FX_MODE_FIRE_FLICKER_SOFT;
  if (modeStr == "FIRE_FLICKER_INTENSE") return FX_MODE_FIRE_FLICKER_INTENSE;
  if (modeStr == "CIRCUS_COMBUSTUS") return FX_MODE_CIRCUS_COMBUSTUS;
  if (modeStr == "HALLOWEEN") return FX_MODE_HALLOWEEN;
  if (modeStr == "BICOLOR_CHASE") return FX_MODE_BICOLOR_CHASE;
  if (modeStr == "TRICOLOR_CHASE") return FX_MODE_TRICOLOR_CHASE;
  if (modeStr == "TWINKLEFOX") return FX_MODE_TWINKLEFOX;
  if (modeStr == "RAIN") return FX_MODE_RAIN;
  if (modeStr == "BLOCK_DISSOLVE") return FX_MODE_BLOCK_DISSOLVE;
  if (modeStr == "ICU") return FX_MODE_ICU;
  if (modeStr == "DUAL_LARSON") return FX_MODE_DUAL_LARSON;
  if (modeStr == "RUNNING_RANDOM2") return FX_MODE_RUNNING_RANDOM2;
  if (modeStr == "FILLER_UP") return FX_MODE_FILLER_UP;
  if (modeStr == "RAINBOW_LARSON") return FX_MODE_RAINBOW_LARSON;
  if (modeStr == "RAINBOW_FIREWORKS") return FX_MODE_RAINBOW_FIREWORKS;
  if (modeStr == "TRIFADE") return FX_MODE_TRIFADE;
  if (modeStr == "VU_METER") return FX_MODE_VU_METER;
  if (modeStr == "HEARTBEAT") return FX_MODE_HEARTBEAT;
  if (modeStr == "BITS") return FX_MODE_BITS;
  if (modeStr == "MULTI_COMET") return FX_MODE_MULTI_COMET;
  if (modeStr == "FLIPBOOK") return FX_MODE_FLIPBOOK;
  if (modeStr == "POPCORN") return FX_MODE_POPCORN;
  if (modeStr == "OSCILLATOR") return FX_MODE_OSCILLATOR;
  return FX_MODE_STATIC; // Default STATIC
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
