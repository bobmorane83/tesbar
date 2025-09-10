#!/usr/bin/env python3
"""
WS2812FX Python Implementation
Recréation des effets lumineux WS2812FX en Python pour simulation de barres LED

Auteur: Assistant IA
Basé sur la bibliothèque WS2812FX Arduino par Harm Aldick
"""

import time
import random
import math
from typing import List, Tuple, Optional, Callable
from enum import Enum


class WS2812FXMode(Enum):
    """Énumération des modes d'effet disponibles"""
    STATIC = 0
    BLINK = 1
    BREATH = 2
    COLOR_WIPE = 3
    COLOR_WIPE_INV = 4
    COLOR_WIPE_REV = 5
    COLOR_WIPE_REV_INV = 6
    COLOR_WIPE_RANDOM = 7
    RANDOM_COLOR = 8
    SINGLE_DYNAMIC = 9
    MULTI_DYNAMIC = 10
    RAINBOW = 11
    RAINBOW_CYCLE = 12
    SCAN = 13
    DUAL_SCAN = 14
    FADE = 15
    THEATER_CHASE = 16
    THEATER_CHASE_RAINBOW = 17
    RUNNING_LIGHTS = 18
    TWINKLE = 19
    TWINKLE_RANDOM = 20
    TWINKLE_FADE = 21
    TWINKLE_FADE_RANDOM = 22
    SPARKLE = 23
    FLASH_SPARKLE = 24
    HYPER_SPARKLE = 25
    STROBE = 26
    STROBE_RAINBOW = 27
    MULTI_STROBE = 28
    BLINK_RAINBOW = 29
    STROBE_RAINBOW_ALT = 30
    CHASE_WHITE = 31
    CHASE_COLOR = 32
    CHASE_RANDOM = 33
    CHASE_RAINBOW = 34
    CHASE_FLASH = 35
    CHASE_FLASH_RANDOM = 36
    CHASE_RAINBOW_WHITE = 37
    CHASE_BLACKOUT = 38
    CHASE_BLACKOUT_RAINBOW = 39
    COLOR_SWEEP_RANDOM = 40
    RUNNING_COLOR = 41
    RUNNING_RED_BLUE = 42
    RUNNING_RANDOM = 43
    LARSON_SCANNER = 44
    COMET = 45
    FIREWORKS = 46
    FIREWORKS_RANDOM = 47
    FIRE_FLICKER = 48
    FIRE_FLICKER_SOFT = 49
    FIRE_FLICKER_INTENSE = 50
    CIRCUS_COMBUSTUS = 51
    HALLOWEEN = 52
    BICOLOR_CHASE = 53
    TRICOLOR_CHASE = 54
    TWINKLEFOX = 55
    RAIN = 56
    BLOCK_DISSOLVE = 57
    ICU = 58
    DUAL_LARSON = 59
    RUNNING_RANDOM2 = 60
    FILLER_UP = 61
    RAINBOW_LARSON = 62
    RAINBOW_FIREWORKS = 63
    TRIFADE = 64
    HEARTBEAT = 65
    VU_METER = 66
    BITS = 67
    MULTI_COMET = 68
    FLIPBOOK = 69
    POPCORN = 70
    OSCILLATOR = 71


class WS2812FXSegment:
    """Classe représentant un segment de LEDs"""

    def __init__(self, start: int, stop: int, mode: WS2812FXMode = WS2812FXMode.STATIC,
                 colors: List[Tuple[int, int, int]] = None, speed: int = 1000,
                 reverse: bool = False):
        self.start = start
        self.stop = stop
        self.mode = mode
        self.colors = colors or [(255, 0, 0)]  # Rouge par défaut
        self.speed = speed
        self.reverse = reverse
        self.length = stop - start + 1

        # Variables d'état pour les animations
        self.counter_mode_step = 0
        self.counter_mode_call = 0
        self.aux_param = 0
        self.aux_param2 = 0
        self.aux_param3 = 0
        self.last_update_time = 0  # Timestamp de la dernière mise à jour


class WS2812FX:
    """
    Classe principale pour les effets WS2812FX en Python
    """

    # Constantes de couleur
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PINK = (255, 192, 203)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)

    def __init__(self, num_leds: int):
        self.num_leds = num_leds
        self.leds = [(0, 0, 0)] * num_leds  # Liste des couleurs RGB des LEDs
        self.segments: List[WS2812FXSegment] = []
        self.brightness = 255
        self.running = False
        self.last_update = time.time()

    def add_segment(self, start: int, stop: int, mode: WS2812FXMode = WS2812FXMode.STATIC,
                   colors: List[Tuple[int, int, int]] = None, speed: int = 1000,
                   reverse: bool = False) -> WS2812FXSegment:
        """Ajoute un segment de LEDs"""
        segment = WS2812FXSegment(start, stop, mode, colors, speed, reverse)
        self.segments.append(segment)
        return segment

    def set_pixel_color(self, index: int, color: Tuple[int, int, int]):
        """Définit la couleur d'une LED"""
        if 0 <= index < self.num_leds:
            self.leds[index] = color

    def get_pixel_color(self, index: int) -> Tuple[int, int, int]:
        """Récupère la couleur d'une LED"""
        if 0 <= index < self.num_leds:
            return self.leds[index]
        return (0, 0, 0)

    def get_segment_colors_safe(self, segment: WS2812FXSegment, index: int) -> Tuple[int, int, int]:
        """Récupère une couleur du segment de manière sécurisée"""
        if segment.colors and 0 <= index < len(segment.colors):
            return segment.colors[index]
        # Couleur par défaut si l'index est hors limites
        return self.get_segment_colors_safe(segment, 0) if segment.colors else (0, 0, 0)

    def fill(self, color: Tuple[int, int, int], start: int = 0, length: int = None):
        """Remplit une plage de LEDs avec une couleur"""
        if length is None:
            length = self.num_leds - start
        for i in range(start, min(start + length, self.num_leds)):
            self.leds[i] = color

    def clear(self):
        """Éteint toutes les LEDs"""
        self.fill(self.BLACK)

    def set_brightness(self, brightness: int):
        """Définit la luminosité globale"""
        self.brightness = max(0, min(255, brightness))

    def get_brightness(self) -> int:
        """Récupère la luminosité globale"""
        return self.brightness

    def start(self):
        """Démarre les animations"""
        self.running = True
        self.last_update = time.time()

    def stop(self):
        """Arrête les animations"""
        self.running = False
        self.clear()

    def update(self):
        """Met à jour les animations"""
        if not self.running:
            return

        current_time = time.time()
        for segment in self.segments:
            self._update_segment(segment)

    def _update_segment(self, segment: WS2812FXSegment):
        """Met à jour un segment spécifique"""
        current_time = time.time()

        # Vérifier si assez de temps s'est écoulé depuis la dernière mise à jour
        if current_time - segment.last_update_time < (segment.speed / 1000.0):
            return

        mode_function = getattr(self, f"mode_{segment.mode.name.lower()}", None)
        if mode_function:
            delay = mode_function(segment)
            segment.counter_mode_call += 1
            segment.last_update_time = current_time



    # Fonctions utilitaires
    def color_blend(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: int) -> Tuple[int, int, int]:
        """Mélange deux couleurs selon un ratio (0-255)"""
        r1, g1, b1 = color1
        r2, g2, b2 = color2

        r = int(r1 + (r2 - r1) * ratio / 255)
        g = int(g1 + (g2 - g1) * ratio / 255)
        b = int(b1 + (b2 - b1) * ratio / 255)

        return (r, g, b)

    def color_wheel(self, wheel_pos: int) -> Tuple[int, int, int]:
        """Génère une couleur de l'arc-en-ciel selon une position (0-255)"""
        wheel_pos = wheel_pos % 256

        if wheel_pos < 85:
            return (255 - wheel_pos * 3, wheel_pos * 3, 0)
        elif wheel_pos < 170:
            wheel_pos -= 85
            return (0, 255 - wheel_pos * 3, wheel_pos * 3)
        else:
            wheel_pos -= 170
            return (wheel_pos * 3, 0, 255 - wheel_pos * 3)

    def sine8(self, angle: int) -> int:
        """Calcule sin(angle) * 255 (angle en 0-255)"""
        return int(255 * math.sin(angle * 2 * math.pi / 256))

    def random8(self, max_val: int = 256) -> int:
        """Génère un nombre aléatoire 0-max_val"""
        return random.randint(0, max_val - 1)

    def random16(self, max_val: int = 65536) -> int:
        """Génère un nombre aléatoire 0-max_val"""
        return random.randint(0, max_val - 1)

    # === MODES D'EFFETS ===

    def mode_static(self, segment: WS2812FXSegment) -> int:
        """Lumière fixe"""
        self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)
        return segment.speed

    def mode_blink(self, segment: WS2812FXSegment) -> int:
        """Clignotement normal"""
        if segment.counter_mode_step % 2 == 0:
            self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)
        else:
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)
        segment.counter_mode_step += 1
        return segment.speed

    def mode_blink_rainbow(self, segment: WS2812FXSegment) -> int:
        """Clignotement arc-en-ciel"""
        color = self.color_wheel((segment.counter_mode_call << 2) & 0xFF)
        if segment.counter_mode_step % 2 == 0:
            self.fill(color, segment.start, segment.length)
        else:
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)
        segment.counter_mode_step += 1
        return segment.speed

    def mode_breath(self, segment: WS2812FXSegment) -> int:
        """Effet respiration"""
        lum = segment.counter_mode_step
        if lum > 255:
            lum = 511 - lum  # 0 -> 255 -> 0

        color = self.color_blend(self.get_segment_colors_safe(segment, 1), self.get_segment_colors_safe(segment, 0), lum)
        self.fill(color, segment.start, segment.length)

        segment.counter_mode_step += 4
        if segment.counter_mode_step > 511:
            segment.counter_mode_step = 0

        return segment.speed // 128

    def mode_fade(self, segment: WS2812FXSegment) -> int:
        """Fondu entre deux couleurs"""
        lum = segment.counter_mode_step
        if lum > 255:
            lum = 511 - lum  # 0 -> 255 -> 0

        color = self.color_blend(self.get_segment_colors_safe(segment, 1), self.get_segment_colors_safe(segment, 0), lum)
        self.fill(color, segment.start, segment.length)

        segment.counter_mode_step += 4
        if segment.counter_mode_step > 511:
            segment.counter_mode_step = 0

        return segment.speed // 128

    def mode_color_wipe(self, segment: WS2812FXSegment) -> int:
        """Balayage de couleur"""
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0
            # Remplir avec la couleur de fond
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        return segment.speed // segment.length

    def mode_color_wipe_inv(self, segment: WS2812FXSegment) -> int:
        """Balayage de couleur inversé"""
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 1))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0
            # Remplir avec la couleur principale
            self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)

        return segment.speed // segment.length

    def mode_color_wipe_rev(self, segment: WS2812FXSegment) -> int:
        """Balayage de couleur en sens inverse"""
        return self.mode_color_wipe(segment)

    def mode_color_wipe_rev_inv(self, segment: WS2812FXSegment) -> int:
        """Balayage de couleur inversé en sens inverse"""
        return self.mode_color_wipe_inv(segment)

    def mode_color_wipe_random(self, segment: WS2812FXSegment) -> int:
        """Balayage de couleur aléatoire"""
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            color = self.color_wheel(self.random8())
            self.set_pixel_color(pos, color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0

        return segment.speed // segment.length

    def mode_random_color(self, segment: WS2812FXSegment) -> int:
        """Couleur aléatoire"""
        for i in range(segment.start, segment.stop + 1):
            self.set_pixel_color(i, self.color_wheel(self.random8()))
        return segment.speed

    def mode_single_dynamic(self, segment: WS2812FXSegment) -> int:
        """Dynamique simple"""
        if segment.counter_mode_step < segment.length:
            if segment.reverse:
                pos = segment.stop - segment.counter_mode_step
            else:
                pos = segment.start + segment.counter_mode_step
            self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length * 2:
            segment.counter_mode_step = 0
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        return segment.speed // segment.length

    def mode_multi_dynamic(self, segment: WS2812FXSegment) -> int:
        """Dynamique multiple"""
        for i in range(segment.start, segment.stop + 1):
            self.set_pixel_color(i, self.color_wheel(self.random8()))
        return segment.speed

    def mode_rainbow(self, segment: WS2812FXSegment) -> int:
        """Arc-en-ciel fixe"""
        for i in range(segment.length):
            if segment.reverse:
                pos = segment.stop - i
            else:
                pos = segment.start + i
            color = self.color_wheel((i * 256 // segment.length) & 0xFF)
            self.set_pixel_color(pos, color)
        return segment.speed

    def mode_rainbow_cycle(self, segment: WS2812FXSegment) -> int:
        """Arc-en-ciel cyclique"""
        for i in range(segment.length):
            if segment.reverse:
                pos = segment.stop - i
            else:
                pos = segment.start + i
            color = self.color_wheel(((i * 256 // segment.length) + segment.counter_mode_call) & 0xFF)
            self.set_pixel_color(pos, color)
        return segment.speed // 4

    def mode_scan(self, segment: WS2812FXSegment) -> int:
        """Balayage"""
        # Ensure we have at least 2 colors
        if len(segment.colors) < 2:
            bg_color = self.get_segment_colors_safe(segment, 0) if segment.colors else (0, 0, 0)
            fg_color = bg_color
        else:
            bg_color = self.get_segment_colors_safe(segment, 1)
            fg_color = self.get_segment_colors_safe(segment, 0)

        self.fill(bg_color, segment.start, segment.length)

        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            self.set_pixel_color(pos, fg_color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0

        return segment.speed // (segment.length * 2)

    def mode_dual_scan(self, segment: WS2812FXSegment) -> int:
        """Balayage double"""
        self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        pos1 = segment.start + segment.counter_mode_step
        pos2 = segment.stop - segment.counter_mode_step

        if pos1 <= pos2:
            if pos1 >= segment.start and pos1 <= segment.stop:
                self.set_pixel_color(pos1, self.get_segment_colors_safe(segment, 0))
            if pos2 >= segment.start and pos2 <= segment.stop:
                self.set_pixel_color(pos2, self.get_segment_colors_safe(segment, 0))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length // 2:
            segment.counter_mode_step = 0

        return segment.speed // (segment.length * 2)

    def mode_theater_chase(self, segment: WS2812FXSegment) -> int:
        """Chasse de théâtre"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 3 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 1))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 3:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_theater_chase_rainbow(self, segment: WS2812FXSegment) -> int:
        """Chasse de théâtre arc-en-ciel"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 3 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                color = self.color_wheel((i * 256 // segment.length + segment.counter_mode_call) & 0xFF)
                self.set_pixel_color(pos, color)
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 1))

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 3:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_white(self, segment: WS2812FXSegment) -> int:
        """Chasse avec couleur blanche"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (255, 255, 255))  # Blanc
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_color(self, segment: WS2812FXSegment) -> int:
        """Chasse avec la couleur du segment"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_random(self, segment: WS2812FXSegment) -> int:
        """Chasse avec couleurs aléatoires"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                # Couleur aléatoire basée sur la position et le compteur
                random_color = (
                    (segment.counter_mode_call + i * 37) % 256,
                    (segment.counter_mode_call + i * 71) % 256,
                    (segment.counter_mode_call + i * 113) % 256
                )
                self.set_pixel_color(pos, random_color)
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_rainbow(self, segment: WS2812FXSegment) -> int:
        """Chasse arc-en-ciel"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                color = self.color_wheel((i * 256 // segment.length + segment.counter_mode_call) & 0xFF)
                self.set_pixel_color(pos, color)
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_flash(self, segment: WS2812FXSegment) -> int:
        """Chasse avec effet flash"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                # Effet flash : alternance rapide
                if segment.counter_mode_call % 2 == 0:
                    self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))
                else:
                    self.set_pixel_color(pos, (255, 255, 255))  # Blanc flash
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed // 2  # Plus rapide pour l'effet flash

    def mode_chase_flash_random(self, segment: WS2812FXSegment) -> int:
        """Chasse flash avec couleurs aléatoires"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                # Couleur aléatoire avec effet flash
                if segment.counter_mode_call % 2 == 0:
                    random_color = (
                        (segment.counter_mode_call + i * 37) % 256,
                        (segment.counter_mode_call + i * 71) % 256,
                        (segment.counter_mode_call + i * 113) % 256
                    )
                    self.set_pixel_color(pos, random_color)
                else:
                    self.set_pixel_color(pos, (255, 255, 255))  # Blanc flash
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed // 2  # Plus rapide pour l'effet flash

    def mode_chase_rainbow_white(self, segment: WS2812FXSegment) -> int:
        """Chasse arc-en-ciel avec fond blanc"""
        for i in range(segment.length):
            if (i + segment.counter_mode_step) % 4 == 0:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                color = self.color_wheel((i * 256 // segment.length + segment.counter_mode_call) & 0xFF)
                self.set_pixel_color(pos, color)
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, (32, 32, 32))  # Blanc très atténué

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 4:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_blackout(self, segment: WS2812FXSegment) -> int:
        """Chasse avec extinction progressive"""
        for i in range(segment.length):
            if segment.reverse:
                pos = segment.stop - i
            else:
                pos = segment.start + i

            # Distance par rapport à la position active
            distance = abs(i - segment.counter_mode_step)

            if distance == 0:
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))  # LED active
            elif distance <= 2:
                # Atténuation progressive
                factor = (3 - distance) / 3
                r = int(self.get_segment_colors_safe(segment, 0)[0] * factor)
                g = int(self.get_segment_colors_safe(segment, 0)[1] * factor)
                b = int(self.get_segment_colors_safe(segment, 0)[2] * factor)
                self.set_pixel_color(pos, (r, g, b))
            else:
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_chase_blackout_rainbow(self, segment: WS2812FXSegment) -> int:
        """Chasse extinction arc-en-ciel"""
        for i in range(segment.length):
            if segment.reverse:
                pos = segment.stop - i
            else:
                pos = segment.start + i

            # Distance par rapport à la position active
            distance = abs(i - segment.counter_mode_step)

            if distance == 0:
                # LED active avec couleur arc-en-ciel
                color = self.color_wheel((i * 256 // segment.length + segment.counter_mode_call) & 0xFF)
                self.set_pixel_color(pos, color)
            elif distance <= 2:
                # Atténuation progressive avec couleur arc-en-ciel
                factor = (3 - distance) / 3
                color = self.color_wheel((i * 256 // segment.length + segment.counter_mode_call) & 0xFF)
                r = int(color[0] * factor)
                g = int(color[1] * factor)
                b = int(color[2] * factor)
                self.set_pixel_color(pos, (r, g, b))
            else:
                self.set_pixel_color(pos, (0, 0, 0))  # Noir

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0

        return segment.speed

    def mode_running_lights(self, segment: WS2812FXSegment) -> int:
        """Lumières courantes avec transition sinusoïdale"""
        size = 1
        sine_incr = (256 // segment.length) * size
        sine_incr = max(sine_incr, 1)

        for i in range(segment.length):
            lum = self.sine8((i + segment.counter_mode_step) * sine_incr)
            color = self.color_blend(self.get_segment_colors_safe(segment, 0), self.get_segment_colors_safe(segment, 1), lum)
            if segment.reverse:
                pos = segment.stop - i
            else:
                pos = segment.start + i
            self.set_pixel_color(pos, color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= 256:
            segment.counter_mode_step = 0

        return segment.speed // 128

    def mode_twinkle(self, segment: WS2812FXSegment) -> int:
        """Scintillement"""
        # Éteindre les LEDs qui scintillent
        for i in range(segment.start, segment.stop + 1):
            color = self.get_pixel_color(i)
            if color != self.get_segment_colors_safe(segment, 1):
                # Fade out
                r, g, b = color
                r = max(0, r - 20)
                g = max(0, g - 20)
                b = max(0, b - 20)
                if r == 0 and g == 0 and b == 0:
                    self.set_pixel_color(i, self.get_segment_colors_safe(segment, 1))
                else:
                    self.set_pixel_color(i, (r, g, b))

        # Allumer quelques LEDs aléatoirement
        if self.random8(3) == 0:
            pos = segment.start + self.random8(segment.length)
            if self.get_pixel_color(pos) == self.get_segment_colors_safe(segment, 1):
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))

        return segment.speed // 32

    def mode_twinkle_random(self, segment: WS2812FXSegment) -> int:
        """Scintillement aléatoire"""
        # Éteindre les LEDs qui scintillent
        for i in range(segment.start, segment.stop + 1):
            color = self.get_pixel_color(i)
            if color != self.get_segment_colors_safe(segment, 1):
                # Fade out
                r, g, b = color
                r = max(0, r - 20)
                g = max(0, g - 20)
                b = max(0, b - 20)
                if r == 0 and g == 0 and b == 0:
                    self.set_pixel_color(i, self.get_segment_colors_safe(segment, 1))
                else:
                    self.set_pixel_color(i, (r, g, b))

        # Allumer quelques LEDs avec des couleurs aléatoires
        if self.random8(3) == 0:
            pos = segment.start + self.random8(segment.length)
            if self.get_pixel_color(pos) == self.get_segment_colors_safe(segment, 1):
                color = self.color_wheel(self.random8())
                self.set_pixel_color(pos, color)

        return segment.speed // 32

    def mode_sparkle(self, segment: WS2812FXSegment) -> int:
        """Étincelle"""
        self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)

        # Ajouter des étincelles blanches aléatoirement
        if self.random8(5) == 0:
            pos = segment.start + self.random8(segment.length)
            self.set_pixel_color(pos, self.WHITE)

        return segment.speed // 32

    def mode_flash_sparkle(self, segment: WS2812FXSegment) -> int:
        """Étincelle flash"""
        self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)

        # Ajouter des étincelles blanches aléatoirement
        if self.random8(5) == 0:
            pos = segment.start + self.random8(segment.length)
            self.set_pixel_color(pos, self.WHITE)

        return segment.speed // 32

    def mode_hyper_sparkle(self, segment: WS2812FXSegment) -> int:
        """Hyper étincelle"""
        self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)

        # Ajouter plusieurs étincelles blanches
        for _ in range(8):
            pos = segment.start + self.random8(segment.length)
            self.set_pixel_color(pos, self.WHITE)

        return segment.speed // 32

    def mode_strobe(self, segment: WS2812FXSegment) -> int:
        """Stroboscope"""
        if segment.counter_mode_step % 2 == 0:
            self.fill(self.get_segment_colors_safe(segment, 0), segment.start, segment.length)
        else:
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        segment.counter_mode_step += 1
        return 50  # Très rapide

    def mode_strobe_rainbow(self, segment: WS2812FXSegment) -> int:
        """Stroboscope arc-en-ciel"""
        if segment.counter_mode_step % 2 == 0:
            color = self.color_wheel((segment.counter_mode_call << 2) & 0xFF)
            self.fill(color, segment.start, segment.length)
        else:
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        segment.counter_mode_step += 1
        return 50  # Très rapide

    def mode_larson_scanner(self, segment: WS2812FXSegment) -> int:
        """Scanner Larson (K.I.T.T.)"""
        self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        # Position du scanner
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 0))

            # Ajouter un effet de traînée
            if pos > segment.start:
                trail_pos = pos - 1 if not segment.reverse else pos + 1
                if trail_pos >= segment.start and trail_pos <= segment.stop:
                    trail_color = self.color_blend(self.get_segment_colors_safe(segment, 0), self.get_segment_colors_safe(segment, 1), 128)
                    self.set_pixel_color(trail_pos, trail_color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0
            segment.reverse = not segment.reverse

        return segment.speed // (segment.length * 2)

    def mode_comet(self, segment: WS2812FXSegment) -> int:
        """Comète"""
        self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        # Position de la comète
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        # Taille de la comète
        comet_size = min(5, segment.length // 4)

        for i in range(comet_size):
            comet_pos = pos - i if not segment.reverse else pos + i
            if comet_pos >= segment.start and comet_pos <= segment.stop:
                intensity = 255 - (i * 255 // comet_size)
                color = self.color_blend(self.get_segment_colors_safe(segment, 0), self.get_segment_colors_safe(segment, 1), intensity)
                self.set_pixel_color(comet_pos, color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length + comet_size:
            segment.counter_mode_step = 0

        return segment.speed // segment.length

    def mode_fireworks(self, segment: WS2812FXSegment) -> int:
        """Feux d'artifice"""
        # Fade out all pixels
        for i in range(segment.start, segment.stop + 1):
            color = self.get_pixel_color(i)
            r, g, b = color
            r = max(0, r - 10)
            g = max(0, g - 10)
            b = max(0, b - 10)
            self.set_pixel_color(i, (r, g, b))

        # Launch new firework occasionally
        if self.random8(20) == 0:
            pos = segment.start + self.random8(segment.length)
            self.set_pixel_color(pos, self.WHITE)

        return segment.speed // 32

    def mode_fire_flicker(self, segment: WS2812FXSegment) -> int:
        """Flamme qui vacille"""
        for i in range(segment.start, segment.stop + 1):
            # Simuler le vacillement d'une flamme
            flicker = self.random8(55) + 200  # 200-255
            r = min(255, self.get_segment_colors_safe(segment, 0)[0] * flicker // 255)
            g = min(255, self.get_segment_colors_safe(segment, 0)[1] * flicker // 255)
            b = min(255, self.get_segment_colors_safe(segment, 0)[2] * flicker // 255)
            self.set_pixel_color(i, (r, g, b))

        return segment.speed // 16

    def mode_fire_flicker_soft(self, segment: WS2812FXSegment) -> int:
        """Flamme qui vacille doucement"""
        for i in range(segment.start, segment.stop + 1):
            # Simuler le vacillement d'une flamme douce
            flicker = self.random8(40) + 215  # 215-255 (plus doux)
            r = min(255, self.get_segment_colors_safe(segment, 0)[0] * flicker // 255)
            g = min(255, self.get_segment_colors_safe(segment, 0)[1] * flicker // 255)
            b = min(255, self.get_segment_colors_safe(segment, 0)[2] * flicker // 255)
            self.set_pixel_color(i, (r, g, b))

        return segment.speed // 12  # Plus lent

    def mode_fire_flicker_intense(self, segment: WS2812FXSegment) -> int:
        """Flamme qui vacille intensément"""
        for i in range(segment.start, segment.stop + 1):
            # Simuler le vacillement d'une flamme intense
            flicker = self.random8(80) + 175  # 175-255 (plus intense)
            r = min(255, self.get_segment_colors_safe(segment, 0)[0] * flicker // 255)
            g = min(255, self.get_segment_colors_safe(segment, 0)[1] * flicker // 255)
            b = min(255, self.get_segment_colors_safe(segment, 0)[2] * flicker // 255)
            self.set_pixel_color(i, (r, g, b))

        return segment.speed // 20  # Plus rapide

    def mode_rainbow_larson(self, segment: WS2812FXSegment) -> int:
        """Scanner Larson arc-en-ciel"""
        self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        # Position du scanner
        if segment.reverse:
            pos = segment.stop - segment.counter_mode_step
        else:
            pos = segment.start + segment.counter_mode_step

        if pos >= segment.start and pos <= segment.stop:
            color = self.color_wheel((segment.counter_mode_call << 4) & 0xFF)
            self.set_pixel_color(pos, color)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= segment.length:
            segment.counter_mode_step = 0
            segment.reverse = not segment.reverse

        return segment.speed // (segment.length * 2)

    def mode_heartbeat(self, segment: WS2812FXSegment) -> int:
        """Battement de cœur"""
        # Pattern de battement: deux pulsations rapprochées
        beat_pattern = [0, 0, 255, 255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if segment.counter_mode_step < len(beat_pattern):
            intensity = beat_pattern[segment.counter_mode_step]
            color = self.color_blend(self.get_segment_colors_safe(segment, 1), self.get_segment_colors_safe(segment, 0), intensity)
            self.fill(color, segment.start, segment.length)
        else:
            self.fill(self.get_segment_colors_safe(segment, 1), segment.start, segment.length)

        segment.counter_mode_step += 1
        if segment.counter_mode_step >= len(beat_pattern) * 2:
            segment.counter_mode_step = 0

        return segment.speed // 16

    def mode_vu_meter(self, segment: WS2812FXSegment) -> int:
        """VU-mètre"""
        # Simuler un niveau audio aléatoire
        level = self.random8(segment.length)

        for i in range(segment.length):
            if i < level:
                # Couleur basée sur le niveau
                ratio = i * 255 // segment.length
                color = self.color_blend(self.GREEN, self.RED, ratio)
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, color)
            else:
                if segment.reverse:
                    pos = segment.stop - i
                else:
                    pos = segment.start + i
                self.set_pixel_color(pos, self.get_segment_colors_safe(segment, 1))

        return segment.speed // 16

    def mode_rain(self, segment: WS2812FXSegment) -> int:
        """Pluie"""
        # Fade out all pixels
        for i in range(segment.start, segment.stop + 1):
            color = self.get_pixel_color(i)
            r, g, b = color
            r = max(0, r - 5)
            g = max(0, g - 5)
            b = max(0, b - 5)
            self.set_pixel_color(i, (r, g, b))

        # Add new raindrops
        if self.random8(10) == 0:
            pos = segment.start + self.random8(segment.length)
            # Couleur bleue pour simuler l'eau
            self.set_pixel_color(pos, (0, 0, 255))

        return segment.speed // 32




# Fonction utilitaire pour tester
def demo_ws2812fx():
    """Démonstration des effets WS2812FX"""
    print("=== Démonstration WS2812FX Python ===")

    # Créer une instance avec 16 LEDs
    ws2812fx = WS2812FX(16)

    # Ajouter quelques segments avec différents effets
    ws2812fx.add_segment(0, 4, WS2812FXMode.RAINBOW_CYCLE, [(255, 0, 0)], 1000)
    ws2812fx.add_segment(5, 9, WS2812FXMode.LARSON_SCANNER, [(0, 255, 0)], 1500)
    ws2812fx.add_segment(10, 15, WS2812FXMode.TWINKLE, [(0, 0, 255)], 2000)

    # Démarrer les animations
    ws2812fx.start()

    print("Effets disponibles:")
    for mode in WS2812FXMode:
        print(f"  {mode.value}: {mode.name}")

    print(f"\nSegments configurés: {len(ws2812fx.segments)}")
    for i, seg in enumerate(ws2812fx.segments):
        print(f"  Segment {i}: LEDs {seg.start}-{seg.stop}, Mode: {seg.mode.name}")

    return ws2812fx


if __name__ == "__main__":
    demo_ws2812fx()
