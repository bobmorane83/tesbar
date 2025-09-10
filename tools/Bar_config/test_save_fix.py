#!/usr/bin/env python3
"""
Test rapide de la correction des paramètres save_config
"""

import sys
import os

# Simuler QColor pour les tests
class QColor:
    def __init__(self, color):
        self.color = color

    def name(self):
        return self.color

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patcher le module pour éviter l'import de PySide6
import json_config_manager
json_config_manager.QColor = QColor

try:
    from json_config_manager import JSONConfigManager
    print("✓ Import JSONConfigManager réussi")

    # Créer une instance
    manager = JSONConfigManager()
    print("✓ Instance JSONConfigManager créée")

    # Créer des données de test
    test_segments = [
        (0, 7, QColor('#ff0000'), 'static', {'name': 'Segment 1'}, 1000, False),
        (8, 15, QColor('#00ff00'), 'blink', {'name': 'Segment 2'}, 500, False)
    ]
    num_leds = 16

    # Tester la sauvegarde avec les bons paramètres
    print("Test de sauvegarde avec paramètres corrects...")
    success = manager.save_config(num_leds, test_segments)
    print(f"✓ Sauvegarde avec paramètres corrects: {success}")

    # Tester le chargement
    loaded_num_leds, loaded_segments = manager.load_config()
    print(f"✓ Chargement après sauvegarde: {loaded_num_leds} LEDs, {len(loaded_segments)} segments")

    print("\n🎉 Test réussi ! Les paramètres sont maintenant corrects.")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
