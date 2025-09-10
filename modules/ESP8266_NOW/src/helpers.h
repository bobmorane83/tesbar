#ifndef HELPERS_H
#define HELPERS_H

#include <Arduino.h>
#include <WS2812FX.h>

uint8_t getMode(String modeStr);
uint32_t getColor(String colorStr);
uint32_t extract_bits(const uint8_t *data, uint8_t start_bit, uint8_t length, bool little_endian);

#endif
