#!/usr/bin/env python3
"""
Simulateur de barre LED avec catalogue d'animations
Nécessite : pip install PySide6
"""

import sys
import json
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QListWidget, QGroupBox,
                              QLabel, QSpinBox, QColorDialog, QComboBox, QCheckBox,
                              QFileDialog, QMessageBox, QDialog, QFormLayout,
                              QLineEdit, QSlider, QListWidgetItem)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import QRect

class Animation:
    """Classe pour définir une animation"""
    def __init__(self, name, animation_type, parameters):
        self.name = name
        self.type = animation_type
        self.parameters = parameters
        self.position = 0
        self.direction = parameters.get('direction', 1)
    
    def to_dict(self):
        """Convertit l'animation en dictionnaire pour JSON"""
        return {
            'name': self.name,
            'type': self.type,
            'parameters': self.parameters
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crée une animation depuis un dictionnaire"""
        return cls(data['name'], data['type'], data['parameters'])

class AnimationEditor(QDialog):
    """Éditeur d'animation"""
    def __init__(self, parent=None, animation=None):
        super().__init__(parent)
        self.animation = animation
        self.init_ui()
        
        if animation:
            self.load_animation(animation)
    
    def init_ui(self):
        self.setWindowTitle("Éditeur d'Animation")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Formulaire principal
        form_layout = QFormLayout()
        
        # Nom
        self.name_edit = QLineEdit()
        form_layout.addRow("Nom:", self.name_edit)
        
        # Type d'animation
        self.type_combo = QComboBox()
        self.type_combo.addItems(["moving_bar", "all_on", "all_off", "wave", "blink"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Type:", self.type_combo)
        
        layout.addLayout(form_layout)
        
        # Paramètres dynamiques
        self.params_group = QGroupBox("Paramètres")
        self.params_layout = QFormLayout(self.params_group)
        layout.addWidget(self.params_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Initialiser les paramètres
        self.on_type_changed("moving_bar")
    
    def clear_params(self):
        """Supprime tous les widgets de paramètres"""
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def on_type_changed(self, animation_type):
        """Met à jour les paramètres selon le type d'animation"""
        self.clear_params()
        
        if animation_type == "moving_bar":
            # Largeur de la barre
            self.width_spin = QSpinBox()
            self.width_spin.setRange(1, 50)
            self.width_spin.setValue(10)
            self.params_layout.addRow("Largeur:", self.width_spin)
            
            # Vitesse
            self.speed_slider = QSlider(Qt.Horizontal)
            self.speed_slider.setRange(10, 200)
            self.speed_slider.setValue(50)
            self.speed_label = QLabel("50 ms")
            self.speed_slider.valueChanged.connect(
                lambda v: self.speed_label.setText(f"{v} ms")
            )
            speed_layout = QHBoxLayout()
            speed_layout.addWidget(self.speed_slider)
            speed_layout.addWidget(self.speed_label)
            self.params_layout.addRow("Vitesse:", speed_layout)
            
            # Couleur
            self.color_button = QPushButton("Choisir couleur")
            self.color_button.setStyleSheet("background-color: #00FF00")
            self.color_button.clicked.connect(self.choose_color)
            self.current_color = QColor(0, 255, 0)
            self.params_layout.addRow("Couleur:", self.color_button)
            
            # Direction
            self.bidirectional_check = QCheckBox("Bidirectionnel")
            self.bidirectional_check.setChecked(True)
            self.params_layout.addRow("", self.bidirectional_check)
            
        elif animation_type == "all_on":
            # Couleur
            self.color_button = QPushButton("Choisir couleur")
            self.color_button.setStyleSheet("background-color: #FFFFFF")
            self.color_button.clicked.connect(self.choose_color)
            self.current_color = QColor(255, 255, 255)
            self.params_layout.addRow("Couleur:", self.color_button)
            
            # Intensité
            self.intensity_slider = QSlider(Qt.Horizontal)
            self.intensity_slider.setRange(10, 100)
            self.intensity_slider.setValue(100)
            self.intensity_label = QLabel("100%")
            self.intensity_slider.valueChanged.connect(
                lambda v: self.intensity_label.setText(f"{v}%")
            )
            intensity_layout = QHBoxLayout()
            intensity_layout.addWidget(self.intensity_slider)
            intensity_layout.addWidget(self.intensity_label)
            self.params_layout.addRow("Intensité:", intensity_layout)
            
        elif animation_type == "all_off":
            # Pas de paramètres spéciaux
            info_label = QLabel("Éteint toutes les LEDs")
            self.params_layout.addRow("", info_label)
    
    def choose_color(self):
        """Ouvre le sélecteur de couleur"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.color_button.setStyleSheet(
                f"background-color: {color.name()}"
            )
    
    def get_parameters(self):
        """Récupère les paramètres selon le type"""
        animation_type = self.type_combo.currentText()
        params = {}
        
        if animation_type == "moving_bar":
            params = {
                'width': self.width_spin.value(),
                'speed': self.speed_slider.value(),
                'color': [self.current_color.red(), self.current_color.green(), self.current_color.blue()],
                'bidirectional': self.bidirectional_check.isChecked()
            }
        elif animation_type == "all_on":
            params = {
                'color': [self.current_color.red(), self.current_color.green(), self.current_color.blue()],
                'intensity': self.intensity_slider.value() / 100.0
            }
        elif animation_type == "all_off":
            params = {}
        
        return params
    
    def load_animation(self, animation):
        """Charge une animation existante dans l'éditeur"""
        self.name_edit.setText(animation.name)
        self.type_combo.setCurrentText(animation.type)
        
        params = animation.parameters
        animation_type = animation.type
        
        if animation_type == "moving_bar" and hasattr(self, 'width_spin'):
            self.width_spin.setValue(params.get('width', 10))
            self.speed_slider.setValue(params.get('speed', 50))
            color = params.get('color', [0, 255, 0])
            self.current_color = QColor(color[0], color[1], color[2])
            self.color_button.setStyleSheet(f"background-color: {self.current_color.name()}")
            self.bidirectional_check.setChecked(params.get('bidirectional', True))
        elif animation_type == "all_on" and hasattr(self, 'intensity_slider'):
            color = params.get('color', [255, 255, 255])
            self.current_color = QColor(color[0], color[1], color[2])
            self.color_button.setStyleSheet(f"background-color: {self.current_color.name()}")
            self.intensity_slider.setValue(int(params.get('intensity', 1.0) * 100))

class LEDBar(QWidget):
    def __init__(self, led_count=120, parent=None):
        super().__init__(parent)
        self.led_count = led_count
        self.led_states = [False] * led_count
        self.led_colors = [QColor(50, 50, 50)] * led_count
        
        # Animation courante
        self.current_animation = None
        
        # Taille du widget
        self.setMinimumSize(1200, 60)
        self.setStyleSheet("background-color: black;")
    
    def paintEvent(self, event):
        """Dessine la barre de LEDs"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        widget_width = self.width() - 40
        led_diameter = 8
        led_spacing = widget_width / self.led_count
        
        start_x = 20
        center_y = self.height() // 2
        
        for i in range(self.led_count):
            center_x = start_x + i * led_spacing + led_spacing / 2
            
            if self.led_states[i]:
                color = self.led_colors[i]
                painter.setPen(QPen(color.lighter(150), 2))
                painter.setBrush(color)
            else:
                color = QColor(20, 20, 20)
                painter.setPen(QPen(QColor(60, 60, 60), 1))
                painter.setBrush(color)
            
            painter.drawEllipse(
                int(center_x - led_diameter/2), 
                int(center_y - led_diameter/2), 
                led_diameter, 
                led_diameter
            )
            
            if self.led_states[i]:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color.lighter(180))
                painter.drawEllipse(
                    int(center_x - 2), 
                    int(center_y - 2), 
                    4, 4
                )
    
    def set_led(self, index, state, color=None):
        if 0 <= index < self.led_count:
            self.led_states[index] = state
            if color:
                self.led_colors[index] = color
            self.update()
    
    def clear_all(self):
        self.led_states = [False] * self.led_count
        self.update()
    
    def set_animation(self, animation):
        """Définit l'animation courante"""
        self.current_animation = animation
        if animation:
            animation.position = 0
            animation.direction = animation.parameters.get('direction', 1)
    
    def update_animation(self):
        """Met à jour l'animation courante"""
        if not self.current_animation:
            return
        
        animation = self.current_animation
        
        if animation.type == "moving_bar":
            self.update_moving_bar(animation)
        elif animation.type == "all_on":
            self.update_all_on(animation)
        elif animation.type == "all_off":
            self.update_all_off(animation)
    
    def update_moving_bar(self, animation):
        """Animation barre mobile"""
        self.clear_all()
        
        params = animation.parameters
        width = params.get('width', 10)
        color_rgb = params.get('color', [0, 255, 0])
        bidirectional = params.get('bidirectional', True)
        
        center_pos = width // 2
        
        for i in range(width):
            led_index = animation.position + i
            
            if 0 <= led_index < self.led_count:
                distance_from_center = abs(i - center_pos)
                max_distance = center_pos
                
                if max_distance > 0:
                    intensity = 1.0 - (distance_from_center / max_distance) * 0.7
                else:
                    intensity = 1.0
                
                color = QColor(
                    int(color_rgb[0] * intensity),
                    int(color_rgb[1] * intensity),
                    int(color_rgb[2] * intensity)
                )
                self.set_led(led_index, True, color)
        
        # Mouvement
        animation.position += animation.direction
        
        if bidirectional:
            if animation.direction == 1:
                if animation.position + width >= self.led_count:
                    animation.direction = -1
                    animation.position = self.led_count - width
            else:
                if animation.position <= 0:
                    animation.direction = 1
                    animation.position = 0
        else:
            if animation.position >= self.led_count:
                animation.position = -width
    
    def update_all_on(self, animation):
        """Animation toutes LEDs allumées"""
        params = animation.parameters
        color_rgb = params.get('color', [255, 255, 255])
        intensity = params.get('intensity', 1.0)
        
        color = QColor(
            int(color_rgb[0] * intensity),
            int(color_rgb[1] * intensity),
            int(color_rgb[2] * intensity)
        )
        
        for i in range(self.led_count):
            self.set_led(i, True, color)
    
    def update_all_off(self, animation):
        """Animation toutes LEDs éteintes"""
        self.clear_all()

class LEDSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.animations = []
        self.init_default_animations()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_current_animation)
        self.init_ui()
    
    def init_default_animations(self):
        """Crée les animations par défaut"""
        # Barre mobile
        moving_bar = Animation("Barre Mobile", "moving_bar", {
            'width': 10,
            'speed': 50,
            'color': [0, 255, 0],
            'bidirectional': True
        })
        
        # Toutes allumées
        all_on = Animation("Toutes Allumées", "all_on", {
            'color': [255, 255, 255],
            'intensity': 1.0
        })
        
        # Toutes éteintes
        all_off = Animation("Toutes Éteintes", "all_off", {})
        
        self.animations = [moving_bar, all_on, all_off]
    
    def init_ui(self):
        self.setWindowTitle("Catalogue d'Animations LED")
        self.setGeometry(100, 100, 1400, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Panel de gauche - Contrôles
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # Liste des animations
        animations_group = QGroupBox("Animations")
        animations_layout = QVBoxLayout(animations_group)
        
        self.animation_list = QListWidget()
        self.animation_list.itemClicked.connect(self.on_animation_selected)
        animations_layout.addWidget(self.animation_list)
        
        # Boutons d'animation
        anim_buttons_layout = QHBoxLayout()
        self.new_button = QPushButton("Nouveau")
        self.new_button.clicked.connect(self.new_animation)
        self.edit_button = QPushButton("Éditer")
        self.edit_button.clicked.connect(self.edit_animation)
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.delete_animation)
        
        anim_buttons_layout.addWidget(self.new_button)
        anim_buttons_layout.addWidget(self.edit_button)
        anim_buttons_layout.addWidget(self.delete_button)
        animations_layout.addLayout(anim_buttons_layout)
        
        left_layout.addWidget(animations_group)
        
        # Contrôles de lecture
        playback_group = QGroupBox("Lecture")
        playback_layout = QVBoxLayout(playback_group)
        
        self.play_button = QPushButton("Jouer")
        self.play_button.clicked.connect(self.play_animation)
        self.stop_button = QPushButton("Arrêter")
        self.stop_button.clicked.connect(self.stop_animation)
        
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.stop_button)
        
        left_layout.addWidget(playback_group)
        
        # Import/Export
        file_group = QGroupBox("Fichiers")
        file_layout = QVBoxLayout(file_group)
        
        self.export_all_button = QPushButton("Exporter Tout")
        self.export_all_button.clicked.connect(self.export_all_animations)
        self.export_selected_button = QPushButton("Exporter Sélection")
        self.export_selected_button.clicked.connect(self.export_selected_animations)
        self.import_button = QPushButton("Importer")
        self.import_button.clicked.connect(self.import_animations)
        
        file_layout.addWidget(self.export_all_button)
        file_layout.addWidget(self.export_selected_button)
        file_layout.addWidget(self.import_button)
        
        left_layout.addWidget(file_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # Panel de droite - LEDs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.led_bar = LEDBar(120)
        right_layout.addWidget(self.led_bar)
        
        main_layout.addWidget(right_panel, 1)
        
        self.update_animation_list()
    
    def update_animation_list(self):
        """Met à jour la liste des animations"""
        self.animation_list.clear()
        for animation in self.animations:
            item = QListWidgetItem(f"{animation.name} ({animation.type})")
            item.setData(Qt.UserRole, animation)
            self.animation_list.addItem(item)
    
    def on_animation_selected(self, item):
        """Animation sélectionnée dans la liste"""
        animation = item.data(Qt.UserRole)
        self.led_bar.set_animation(animation)
    
    def new_animation(self):
        """Crée une nouvelle animation"""
        editor = AnimationEditor(self)
        if editor.exec():
            name = editor.name_edit.text() or "Nouvelle Animation"
            animation_type = editor.type_combo.currentText()
            parameters = editor.get_parameters()
            
            animation = Animation(name, animation_type, parameters)
            self.animations.append(animation)
            self.update_animation_list()
    
    def edit_animation(self):
        """Édite l'animation sélectionnée"""
        current_item = self.animation_list.currentItem()
        if not current_item:
            return
        
        animation = current_item.data(Qt.UserRole)
        editor = AnimationEditor(self, animation)
        if editor.exec():
            animation.name = editor.name_edit.text() or animation.name
            animation.type = editor.type_combo.currentText()
            animation.parameters = editor.get_parameters()
            self.update_animation_list()
    
    def delete_animation(self):
        """Supprime l'animation sélectionnée"""
        current_item = self.animation_list.currentItem()
        if not current_item:
            return
        
        animation = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Supprimer", 
                                   f"Supprimer l'animation '{animation.name}' ?")
        if reply == QMessageBox.Yes:
            self.animations.remove(animation)
            self.update_animation_list()
    
    def play_animation(self):
        """Lance l'animation sélectionnée"""
        current_item = self.animation_list.currentItem()
        if not current_item:
            return
        
        animation = current_item.data(Qt.UserRole)
        self.led_bar.set_animation(animation)
        
        speed = animation.parameters.get('speed', 50)
        self.animation_timer.start(speed)
    
    def stop_animation(self):
        """Arrête l'animation"""
        self.animation_timer.stop()
        self.led_bar.clear_all()
    
    def update_current_animation(self):
        """Met à jour l'animation en cours"""
        self.led_bar.update_animation()
    
    def export_all_animations(self):
        """Exporte toutes les animations"""
        if not self.animations:
            QMessageBox.information(self, "Export", "Aucune animation à exporter.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter animations", "", "JSON Files (*.json)"
        )
        if filename:
            self.save_animations_to_file(filename, self.animations)
    
    def export_selected_animations(self):
        """Exporte les animations sélectionnées"""
        selected_items = self.animation_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Export", "Aucune animation sélectionnée.")
            return
        
        selected_animations = [item.data(Qt.UserRole) for item in selected_items]
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter animations sélectionnées", "", "JSON Files (*.json)"
        )
        if filename:
            self.save_animations_to_file(filename, selected_animations)
    
    def save_animations_to_file(self, filename, animations):
        """Sauvegarde les animations dans un fichier JSON"""
        try:
            data = {
                'version': '1.0',
                'led_count': 120,
                'animations': [anim.to_dict() for anim in animations]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Export", 
                                  f"{len(animations)} animation(s) exportée(s) avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'export: {str(e)}")
    
    def import_animations(self):
        """Importe des animations depuis un fichier JSON"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Importer animations", "", "JSON Files (*.json)"
        )
        if filename:
            self.load_animations_from_file(filename)
    
    def load_animations_from_file(self, filename):
        """Charge les animations depuis un fichier JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_animations = []
            for anim_data in data.get('animations', []):
                animation = Animation.from_dict(anim_data)
                imported_animations.append(animation)
            
            # Ajouter à la liste existante
            self.animations.extend(imported_animations)
            self.update_animation_list()
            
            QMessageBox.information(self, "Import", 
                                  f"{len(imported_animations)} animation(s) importée(s) avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
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
        QGroupBox {
            color: white;
            font-weight: bold;
            border: 2px solid #606060;
            border-radius: 4px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QListWidget {
            background-color: #353535;
            color: white;
            border: 1px solid #606060;
        }
        QListWidget::item:selected {
            background-color: #4a9eff;
        }
    """)
    
    window = LEDSimulator()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()