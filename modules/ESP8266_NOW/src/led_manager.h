#pragma once
#include <WS2812FX.h>

class LedManager {
private:
    WS2812FX ws2812fx;
    static const uint8_t MAX_SEGMENTS = 16;
    static const uint32_t COLOR_ON = 0x00FF00;  // Vert
    static const uint32_t COLOR_OFF = 0x000000; // Éteint
    uint8_t num_segments;

public:
    LedManager(uint8_t pin, uint8_t num_leds) : 
        ws2812fx(num_leds, pin, NEO_GRB + NEO_KHZ800),
        num_segments(0) {
    }

    void begin() {
        ws2812fx.init();
        ws2812fx.setBrightness(50);
        ws2812fx.setSpeed(1000);
        ws2812fx.start();
    }

    // Crée un nouveau segment avec index de début, nombre de LEDs et mode
    uint8_t addSegment(uint8_t start_led, uint8_t num_leds, uint8_t mode) {
        if (num_segments >= MAX_SEGMENTS) return 0xFF;
        if (start_led + num_leds > MAX_SEGMENTS) return 0xFF;
        
        uint8_t segment_id = num_segments++;
        ws2812fx.setSegment(segment_id, 
                           start_led,               // première LED du segment
                           start_led + num_leds - 1,// dernière LED du segment
                           mode,                    // mode d'animation
                           COLOR_OFF,               // couleur initiale
                           1000,                    // vitesse
                           false);                  // pas d'inversion
        return segment_id;
    }

    // Version simplifiée pour un segment d'une seule LED en mode statique
    uint8_t addSingleLedSegment(uint8_t led_index) {
        return addSegment(led_index, 1, FX_MODE_STATIC);
    }

    // Met à jour l'état d'un segment (ON/OFF)
    void updateSegment(uint8_t segment_id, bool is_on) {
        if (segment_id >= num_segments) return;
        ws2812fx.setPixelColor(segment_id, is_on ? COLOR_ON : COLOR_OFF);
        ws2812fx.show();
    }

    void update() {
        ws2812fx.service();
    }
};
