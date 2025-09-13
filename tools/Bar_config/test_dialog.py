#!/usr/bin/env python3
"""
Test de la boîte de dialogue de configuration des LEDs
"""

import sys
import os
import tempfile
import shutil

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

    # Créer un répertoire temporaire pour les tests
    test_dir = tempfile.mkdtemp()
    print(f"Test dans le répertoire: {test_dir}")

    # Créer une instance du manager avec un fichier de test
    test_config_file = os.path.join(test_dir, 'test_segments.json')
    manager = JSONConfigManager(test_config_file)
    print("✓ Instance JSONConfigManager créée")

    # Simuler la logique de l'application
    config_file = test_config_file
    if not os.path.exists(config_file):
        print("✓ Fichier de configuration n'existe pas - boîte de dialogue devrait s'ouvrir")
        # Simuler la création d'une configuration par défaut
        num_leds = 16  # Valeur par défaut
        manager.save_config(num_leds, [])
        print(f"✓ Configuration par défaut créée avec {num_leds} LEDs")
    else:
        print("✗ Fichier existe déjà")

    # Tester le chargement
    loaded_num_leds, loaded_segments = manager.load_config()
    print(f"✓ Chargement réussi: {loaded_num_leds} LEDs, {len(loaded_segments)} segments")

    # Nettoyer
    shutil.rmtree(test_dir)
    print("✓ Test terminé avec succès")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
