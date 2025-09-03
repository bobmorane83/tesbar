#!/usr/bin/env python3
"""
Simulateur de barre LED avec animation
Nécessite : pip install PySide6
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRect

class LEDBar(QWidget):
    def __init__(self, led_count=120, parent=None):
        super().__init__(parent)
        self.led_count = led_count
        self.led_states = [False] * led_count  # False = éteint, True = allumé
        self.led_colors = [QColor(50, 50, 50)] * led_count  # Couleur par défaut (gris foncé)
        
        # Animation parameters
        self.animation_position = 0
        self.animation_width = 10
        self.animation_color = QColor(0, 255, 0)  # Vert
        self.animation_direction = 1  # 1 = gauche à droite, -1 = droite à gauche
        
        # Taille du widget (plus petit en hauteur)
        self.setMinimumSize(1200, 60)
        self.setStyleSheet("background-color: black;")
    
    def paintEvent(self, event):
        """Dessine la barre de LEDs"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calcul de l'espacement et taille des LEDs
        widget_width = self.width() - 40  # Marges plus importantes
        led_diameter = 8  # Diamètre fixe pour les LEDs rondes
        led_spacing = widget_width / self.led_count
        
        start_x = 20
        center_y = self.height() // 2
        
        # Dessiner chaque LED comme un petit cercle
        for i in range(self.led_count):
            center_x = start_x + i * led_spacing + led_spacing / 2
            
            # Couleur de la LED
            if self.led_states[i]:
                color = self.led_colors[i]
                # Effet de halo pour les LEDs allumées
                painter.setPen(QPen(color.lighter(150), 2))
                painter.setBrush(color)
            else:
                color = QColor(20, 20, 20)  # Très sombre quand éteinte
                painter.setPen(QPen(QColor(60, 60, 60), 1))
                painter.setBrush(color)
            
            # Dessiner le cercle de la LED
            painter.drawEllipse(
                int(center_x - led_diameter/2), 
                int(center_y - led_diameter/2), 
                led_diameter, 
                led_diameter
            )
            
            # Petit point lumineux au centre si allumée
            if self.led_states[i]:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color.lighter(180))
                painter.drawEllipse(
                    int(center_x - 2), 
                    int(center_y - 2), 
                    4, 4
                )
    
    def set_led(self, index, state, color=None):
        """Allume/éteint une LED avec une couleur optionnelle"""
        if 0 <= index < self.led_count:
            self.led_states[index] = state
            if color:
                self.led_colors[index] = color
            self.update()  # Redessiner
    
    def clear_all(self):
        """Éteint toutes les LEDs"""
        self.led_states = [False] * self.led_count
        self.update()
    
    def update_animation(self):
        """Met à jour l'animation de la barre mobile"""
        # Éteindre toutes les LEDs
        self.clear_all()
        
        # Allumer les LEDs de l'animation avec intensité progressive
        center_pos = self.animation_width // 2
        
        for i in range(self.animation_width):
            led_index = self.animation_position + i
            
            # Vérifier les limites
            if 0 <= led_index < self.led_count:
                # Calcul de l'intensité basé sur la distance au centre
                distance_from_center = abs(i - center_pos)
                max_distance = center_pos
                
                # Intensité de 0.3 (30%) aux bords à 1.0 (100%) au centre
                if max_distance > 0:
                    intensity = 1.0 - (distance_from_center / max_distance) * 0.7
                else:
                    intensity = 1.0
                
                # Appliquer l'intensité à la couleur
                color = QColor(
                    int(self.animation_color.red() * intensity),
                    int(self.animation_color.green() * intensity),
                    int(self.animation_color.blue() * intensity)
                )
                self.set_led(led_index, True, color)
        
        # Avancer la position selon la direction
        self.animation_position += self.animation_direction
        
        # Gérer les changements de direction aux extrémités
        if self.animation_direction == 1:  # Gauche à droite
            if self.animation_position + self.animation_width >= self.led_count:
                self.animation_direction = -1
                self.animation_position = self.led_count - self.animation_width
        else:  # Droite à gauche
            if self.animation_position <= 0:
                self.animation_direction = 1
                self.animation_position = 0

class LEDSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_animation()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Simulateur Barre LED - 120 LEDs")
        self.setGeometry(100, 100, 1300, 200)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Barre de LEDs
        self.led_bar = LEDBar(120)
        layout.addWidget(self.led_bar)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Démarrer Animation")
        self.start_button.clicked.connect(self.start_animation)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Arrêter Animation")
        self.stop_button.clicked.connect(self.stop_animation)
        button_layout.addWidget(self.stop_button)
        
        self.clear_button = QPushButton("Éteindre Tout")
        self.clear_button.clicked.connect(self.led_bar.clear_all)
        button_layout.addWidget(self.clear_button)
        
        layout.addLayout(button_layout)
    
    def setup_animation(self):
        """Configure le timer pour l'animation"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.led_bar.update_animation)
        self.animation_speed = 50  # millisecondes (plus petit = plus rapide)
    
    def start_animation(self):
        """Démarre l'animation"""
        self.animation_timer.start(self.animation_speed)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    
    def stop_animation(self):
        """Arrête l'animation"""
        self.animation_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    
    # Style sombre pour l'application
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QPushButton {
            background-color: #404040;
            color: white;
            border: 1px solid #606060;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #303030;
        }
        QPushButton:disabled {
            background-color: #2b2b2b;
            color: #808080;
        }
    """)
    
    window = LEDSimulator()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()