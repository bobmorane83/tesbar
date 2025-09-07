# WS2812FX Python - Effets Lumineux pour Barres LED

Ce projet contient une implémentation Python complète des effets lumineux WS2812FX, adaptée pour fonctionner avec l'application de configuration de barres LED Tesla.

## 📁 Fichiers

- `ws2812fx_python.py` - Bibliothèque principale des effets WS2812FX
- `ws2812fx_demo.py` - Application de démonstration intégrant WS2812FX
- `led_bar_app.py` - Application originale de configuration (modifiée)

## 🎨 Effets Disponibles

### Modes de Base
- **STATIC** - Lumière fixe
- **BLINK** - Clignotement simple
- **BREATH** - Effet respiration
- **FADE** - Fondu entre couleurs

### Modes de Balayage
- **COLOR_WIPE** - Balayage de couleur
- **SCAN** - Balayage simple
- **DUAL_SCAN** - Balayage double
- **THEATER_CHASE** - Chasse de théâtre
- **RUNNING_LIGHTS** - Lumières courantes

### Modes Arc-en-ciel
- **RAINBOW** - Arc-en-ciel fixe
- **RAINBOW_CYCLE** - Arc-en-ciel cyclique
- **THEATER_CHASE_RAINBOW** - Chasse arc-en-ciel

### Modes Spéciaux
- **TWINKLE** - Scintillement
- **SPARKLE** - Étincelle
- **FLASH_SPARKLE** - Étincelle flash
- **HYPER_SPARKLE** - Hyper étincelle
- **LARSON_SCANNER** - Scanner Larson (K.I.T.T.)
- **COMET** - Comète
- **FIREWORKS** - Feux d'artifice
- **FIRE_FLICKER** - Flamme vacillante
- **HEARTBEAT** - Battement de cœur
- **VU_METER** - VU-mètre
- **RAIN** - Pluie

## 🚀 Utilisation

### Démarrage Rapide

```python
from ws2812fx_python import WS2812FX, WS2812FXMode

# Créer une instance avec 16 LEDs
ws2812fx = WS2812FX(16)

# Ajouter un segment avec effet arc-en-ciel
ws2812fx.add_segment(
    start=0,
    stop=15,
    mode=WS2812FXMode.RAINBOW_CYCLE,
    colors=[(255, 0, 0)],  # Rouge
    speed=1000
)

# Démarrer l'animation
ws2812fx.start()

# Boucle principale
while True:
    ws2812fx.update()
    time.sleep(0.05)  # ~20 FPS
```

### Avec l'Application de Configuration

```bash
cd /Users/macbook/Developpement/Tesla/tesbar/tools/Bar_config
python3 ws2812fx_demo.py
```

L'application de démonstration intègre automatiquement WS2812FX et permet de :
- Configurer des segments LED
- Sélectionner des effets WS2812FX
- Voir la simulation en temps réel
- Sauvegarder/charger des configurations

## 🔧 Architecture

### Classe WS2812FX
Classe principale gérant les effets lumineux.

**Méthodes principales :**
- `add_segment()` - Ajoute un segment d'effet
- `start()` - Démarre les animations
- `stop()` - Arrête les animations
- `update()` - Met à jour les effets
- `set_pixel_color()` - Définit la couleur d'une LED
- `get_pixel_color()` - Récupère la couleur d'une LED

### Classe WS2812FXSegment
Représente un segment de LEDs avec ses paramètres d'effet.

**Attributs :**
- `start/stop` - Plage de LEDs
- `mode` - Effet à appliquer
- `colors` - Couleurs utilisées
- `speed` - Vitesse de l'effet
- `reverse` - Sens de l'animation

## 🎯 Mapping des Modes

L'application mappe automatiquement les modes de configuration vers les effets WS2812FX :

| Mode Configuration | Effet WS2812FX |
|-------------------|----------------|
| static           | STATIC        |
| blinking         | BLINK         |
| breathing        | BREATH        |
| rainbow          | RAINBOW_CYCLE |
| chase            | THEATER_CHASE |
| scanner          | LARSON_SCANNER|
| comet            | COMET         |
| twinkle          | TWINKLE       |
| fireworks        | FIREWORKS     |
| rain             | RAIN          |
| heartbeat        | HEARTBEAT     |
| vu_meter         | VU_METER      |
| fire_flicker     | FIRE_FLICKER  |

## 🎨 Fonctions Utilitaires

### Mélange de Couleurs
```python
color = ws2812fx.color_blend(color1, color2, ratio)  # ratio 0-255
```

### Roue de Couleurs (Arc-en-ciel)
```python
color = ws2812fx.color_wheel(position)  # position 0-255
```

### Nombres Aléatoires
```python
value = ws2812fx.random8(max_val)   # 0 à max_val
value = ws2812fx.random16(max_val)  # 0 à max_val
```

## 🔄 Intégration avec l'Application Existante

Le simulateur `WS2812FXSimulator` intègre automatiquement WS2812FX avec l'application de configuration :

1. **Synchronisation** - Convertit les segments de l'application en segments WS2812FX
2. **Mise à jour temps réel** - Applique les couleurs calculées à la barre LED
3. **Mapping automatique** - Traduit les modes de configuration en effets WS2812FX

## 📊 Performances

- **Fréquence de mise à jour** : ~20 FPS (50ms)
- **Mémoire** : Efficace pour bandes jusqu'à 1000 LEDs
- **CPU** : Optimisé pour animations fluides

## 🎪 Exemples d'Effets

### Arc-en-ciel Cyclique
```python
ws2812fx.add_segment(0, 15, WS2812FXMode.RAINBOW_CYCLE, [(255, 0, 0)], 1000)
```

### Scanner Larson (K.I.T.T.)
```python
ws2812fx.add_segment(0, 15, WS2812FXMode.LARSON_SCANNER, [(255, 0, 0)], 1500)
```

### Feux d'Artifice
```python
ws2812fx.add_segment(0, 15, WS2812FXMode.FIREWORKS, [(255, 255, 255)], 2000)
```

## 🔧 Personnalisation

### Modes Personnalisés
```python
def my_custom_effect(segment):
    # Votre logique d'effet personnalisé
    return 1000  # Retourner le délai en ms

ws2812fx.set_custom_mode(0, my_custom_effect)
ws2812fx.add_segment(0, 15, WS2812FXMode.CUSTOM_0, [(255, 0, 0)], 1000)
```

### Ajustement des Paramètres
- **Vitesse** : Contrôle la rapidité de l'effet (10-5000ms)
- **Couleurs** : Liste de couleurs utilisées par l'effet
- **Sens** : reverse=True pour inverser l'animation

## 📝 Notes Techniques

- Basé sur la bibliothèque Arduino WS2812FX de Harm Aldick
- Adapté pour Python avec PySide6/Qt
- Compatible avec les bandes LED WS2812/NeoPixel
- Support des segments multiples
- Gestion optimisée de la mémoire

## 🎯 Prochaines Étapes

- [ ] Ajouter plus d'effets spécialisés
- [ ] Optimiser les performances pour bandes très longues
- [ ] Ajouter le support des masques de pixels
- [ ] Implémenter la persistance des paramètres
- [ ] Créer une interface de prévisualisation avancée

---

**Auteur** : Assistant IA
**Basé sur** : WS2812FX Arduino Library
**Licence** : MIT (compatible avec l'original)
