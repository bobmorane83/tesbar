"""
JSON Configuration Manager
Gère la lecture et l'écriture des fichiers de configuration JSON pour les segments LED
"""

import json
import os
from PySide6.QtGui import QColor


class JSONConfigManager:
    """Gestionnaire de configuration JSON pour les segments LED"""

    # Configuration par défaut
    DEFAULT_CONFIG = {
        "num_leds": 16,
        "segments": [
            {
                "segment": {
                    "start": 0,
                    "end": 15,
                    "color": "#00ff00",
                    "mode": "static",
                    "speed": 1000,
                    "reverse": False,
                    "name": "Segment par défaut"
                },
                "signal": {}
            }
        ]
    }

    # Modes WS2812FX valides
    VALID_MODES = [
        'static', 'blink', 'breath', 'color_wipe', 'color_wipe_inv',
        'color_wipe_rev', 'color_wipe_rev_inv', 'color_wipe_random',
        'random_color', 'single_dynamic', 'multi_dynamic', 'rainbow',
        'rainbow_cycle', 'scan', 'dual_scan', 'fade', 'theater_chase',
        'theater_chase_rainbow', 'running_lights', 'twinkle',
        'twinkle_random', 'twinkle_fade', 'twinkle_fade_random',
        'sparkle', 'flash_sparkle', 'hyper_sparkle', 'strobe',
        'strobe_rainbow', 'multi_strobe', 'blink_rainbow', 'chase_white',
        'chase_color', 'chase_random', 'chase_rainbow', 'chase_flash',
        'chase_flash_random', 'chase_rainbow_white', 'chase_blackout',
        'chase_blackout_rainbow', 'color_sweep_random', 'running_color',
        'running_red_blue', 'running_random', 'larson_scanner',
        'comet', 'fireworks', 'fireworks_random', 'merry_christmas',
        'fire_flicker', 'fire_flicker_soft', 'fire_flicker_intense',
        'circus_combustus', 'halloween', 'bicolor_chase', 'tricolor_chase',
        'icu', 'custom_0', 'custom_1', 'custom_2', 'custom_3'
    ]

    def __init__(self, config_file='segments.json'):
        """Initialise le gestionnaire de configuration

        Args:
            config_file (str): Chemin vers le fichier de configuration
        """
        self.config_file = config_file

    def validate_config_file(self):
        """Valide l'intégrité du fichier de configuration

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            if not os.path.exists(self.config_file):
                return False, "Fichier de configuration non trouvé"

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return False, "Le fichier JSON n'est pas un objet valide"

            if 'num_leds' not in data:
                return False, "Champ 'num_leds' manquant"

            if 'segments' not in data:
                return False, "Champ 'segments' manquant"

            if not isinstance(data['segments'], list):
                return False, "Le champ 'segments' n'est pas une liste"

            for i, seg in enumerate(data['segments']):
                if not isinstance(seg, dict):
                    return False, f"Segment {i} n'est pas un objet"

                if 'segment' not in seg:
                    return False, f"Segment {i}: champ 'segment' manquant"

                if 'signal' not in seg:
                    return False, f"Segment {i}: champ 'signal' manquant"

            return True, "Configuration valide"

        except json.JSONDecodeError as e:
            return False, f"Erreur de parsing JSON: {e}"
        except Exception as e:
            return False, f"Erreur lors de la validation: {e}"

    def create_default_config(self):
        """Crée une configuration par défaut

        Returns:
            bool: True si la création a réussi, False sinon
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            print("Configuration par défaut créée")
            return True
        except Exception as e:
            print(f"Erreur lors de la création de la configuration par défaut: {e}")
            return False

    def load_config(self):
        """Charge la configuration depuis le fichier JSON avec gestion d'erreurs robuste

        Returns:
            tuple: (num_leds, segments) ou (16, []) en cas d'erreur
        """
        # Validation du fichier avant chargement
        is_valid, error_msg = self.validate_config_file()
        if not is_valid:
            print(f"Configuration invalide: {error_msg}")
            if "non trouvé" in error_msg:
                print("Création d'une configuration par défaut...")
                if self.create_default_config():
                    return self.load_config()  # Rechargement récursif
                else:
                    return 16, []
            else:
                print("Tentative de chargement malgré les erreurs...")

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validation de base de la structure
                if not isinstance(data, dict):
                    print("Erreur: Le fichier JSON n'est pas un objet valide")
                    return 16, []

                num_leds = data.get('num_leds', 16)
                if not isinstance(num_leds, int) or num_leds < 1 or num_leds > 10000:
                    print(f"Avertissement: num_leds invalide ({num_leds}), utilisation de 16 par défaut")
                    num_leds = 16

                segments_data = data.get('segments', [])
                if not isinstance(segments_data, list):
                    print("Erreur: La section 'segments' n'est pas une liste")
                    return num_leds, []

                segments = []
                for i, seg_dict in enumerate(segments_data):
                    try:
                        if not isinstance(seg_dict, dict):
                            print(f"Avertissement: Segment {i} n'est pas un objet, ignoré")
                            continue

                        # Chargement des données du segment
                        segment = seg_dict.get('segment', {})
                        if not isinstance(segment, dict):
                            segment = {}

                        start = segment.get('start', 0)
                        end = segment.get('end', 0)
                        color_str = segment.get('color', '#ff0000')
                        mode = segment.get('mode', 'static')
                        speed = segment.get('speed', 1000)
                        reverse = segment.get('reverse', False)
                        name = segment.get('name', '')  # Charger le nom depuis l'objet segment

                        # Validation des valeurs
                        if not isinstance(start, int) or start < 0:
                            start = 0
                        if not isinstance(end, int) or end < start:
                            end = start
                        if not isinstance(speed, int) or speed < 0:
                            speed = 1000

                        # Conversion de la couleur
                        try:
                            color = QColor(color_str)
                        except:
                            color = QColor('#ff0000')

                        # Chargement des données du signal
                        signal_info = seg_dict.get('signal', {})
                        if not isinstance(signal_info, dict):
                            signal_info = {}

                        # Ajouter le nom du segment à signal_info pour la compatibilité
                        if name:
                            signal_info['name'] = name

                        segments.append((start, end, color, mode, signal_info, speed, reverse))

                    except Exception as e:
                        print(f"Erreur lors du chargement du segment {i}: {e}")
                        continue

                print(f"Configuration chargée: {len(segments)} segments pour {num_leds} LEDs")
                return num_leds, segments

        except json.JSONDecodeError as e:
            print(f"Erreur de parsing JSON: {e}")
        except FileNotFoundError:
            print("Fichier de configuration non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")

        print("Utilisation de la configuration par défaut")
        return 16, []

    def save_config(self, num_leds, segments):
        """Sauvegarde la configuration dans le fichier JSON avec gestion d'erreurs

        Args:
            num_leds (int): Nombre total de LEDs
            segments (list): Liste des segments à sauvegarder

        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            segments_list = []

            for i, seg in enumerate(segments):
                try:
                    start, end, color, mode, signal_info, speed, reverse = seg

                    # Validation des données avant sauvegarde
                    if not isinstance(start, int) or start < 0:
                        start = 0
                    if not isinstance(end, int) or end < start:
                        end = start
                    if not isinstance(speed, int) or speed < 0:
                        speed = 1000

                    # Conversion sécurisée de la couleur
                    try:
                        color_name = color.name()
                    except:
                        color_name = '#ff0000'

                    # Validation du mode
                    if mode.lower() not in [m.lower() for m in self.VALID_MODES]:
                        print(f"Avertissement: Mode '{mode}' invalide pour le segment {i}, utilisation de 'static'")
                        mode = 'static'

                    # Validation de signal_info
                    if not isinstance(signal_info, dict):
                        signal_info = {}

                    # Extraire le nom du segment de signal_info et le mettre dans l'objet segment
                    segment_name = signal_info.get('name', '')

                    # Créer une copie de signal_info sans le champ 'name'
                    signal_info_clean = signal_info.copy()
                    if 'name' in signal_info_clean:
                        del signal_info_clean['name']

                    seg_dict = {
                        'segment': {
                            'start': start,
                            'end': end,
                            'color': color_name,
                            'mode': mode,
                            'speed': speed,
                            'reverse': reverse,
                            'name': segment_name
                        },
                        'signal': signal_info_clean
                    }
                    segments_list.append(seg_dict)

                except Exception as e:
                    print(f"Erreur lors de la préparation du segment {i} pour la sauvegarde: {e}")
                    continue

            data = {
                'num_leds': num_leds,
                'segments': segments_list
            }

            # Création d'une sauvegarde du fichier existant
            if os.path.exists(self.config_file):
                try:
                    os.rename(self.config_file, self.config_file + '.backup')
                except:
                    pass  # Si la sauvegarde échoue, on continue

            # Sauvegarde du nouveau fichier
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"Configuration sauvegardée: {len(segments_list)} segments")
            return True

        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
            # Tentative de restauration de la sauvegarde
            if os.path.exists(self.config_file + '.backup'):
                try:
                    os.rename(self.config_file + '.backup', self.config_file)
                    print("Sauvegarde restaurée")
                except:
                    print("Impossible de restaurer la sauvegarde")
            return False

    def get_config_summary(self):
        """Retourne un résumé de la configuration actuelle

        Returns:
            dict: Résumé de la configuration
        """
        try:
            if not os.path.exists(self.config_file):
                return {"error": "Fichier de configuration non trouvé"}

            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            num_leds = data.get('num_leds', 0)
            segments = data.get('segments', [])

            summary = {
                "num_leds": num_leds,
                "total_segments": len(segments),
                "segments_with_signals": 0,
                "segments_without_signals": 0,
                "modes_used": set(),
                "colors_used": set()
            }

            for seg in segments:
                segment = seg.get('segment', {})
                signal = seg.get('signal', {})

                if signal and any(signal.values()):  # Si le signal a des données
                    summary["segments_with_signals"] += 1
                else:
                    summary["segments_without_signals"] += 1

                mode = segment.get('mode', 'static')
                summary["modes_used"].add(mode)

                color = segment.get('color', '#ff0000')
                summary["colors_used"].add(color)

            summary["modes_used"] = list(summary["modes_used"])
            summary["colors_used"] = list(summary["colors_used"])

            return summary

        except Exception as e:
            return {"error": f"Erreur lors de la lecture du résumé: {e}"}


# Fonctions utilitaires pour la compatibilité
def load_config(config_file='segments.json'):
    """Fonction de compatibilité pour charger la configuration"""
    manager = JSONConfigManager(config_file)
    return manager.load_config()


def save_config(num_leds, segments, config_file='segments.json'):
    """Fonction de compatibilité pour sauvegarder la configuration"""
    manager = JSONConfigManager(config_file)
    return manager.save_config(num_leds, segments)


def validate_config_file(config_file='segments.json'):
    """Fonction de compatibilité pour valider le fichier de configuration"""
    manager = JSONConfigManager(config_file)
    return manager.validate_config_file()


def create_default_config(config_file='segments.json'):
    """Fonction de compatibilité pour créer une configuration par défaut"""
    manager = JSONConfigManager(config_file)
    return manager.create_default_config()


if __name__ == "__main__":
    # Test du module
    manager = JSONConfigManager()

    print("=== Test du JSONConfigManager ===")

    # Test de validation
    is_valid, msg = manager.validate_config_file()
    print(f"Validation: {msg}")

    # Test de chargement
    num_leds, segments = manager.load_config()
    print(f"Chargement: {len(segments)} segments pour {num_leds} LEDs")

    # Test du résumé
    summary = manager.get_config_summary()
    print(f"Résumé: {summary}")

    print("=== Test terminé ===")
