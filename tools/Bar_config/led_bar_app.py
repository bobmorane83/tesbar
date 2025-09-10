from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import json
import os
from dbc_manager import DBCManager
from ws2812fx_python import WS2812FX, WS2812FXMode

class LEDBar(QWidget):
    def __init__(self, num_leds, parent_window):
        super().__init__()
        self.num_leds = num_leds
        self.led_colors = [QColor('gray')] * num_leds
        self.segments = []
        self.selected_segment = None
        self.start_index = None
        self.end_index = None
        self.is_editing = False
        self.parent_window = parent_window
        self.setFixedHeight(50)
        
        # WS2812FX instance for main bar effects
        self.ws2812fx = WS2812FX(num_leds)
        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self.update_effects)
        self.effect_timer.start(50)  # ~20 FPS

    def update_effects(self):
        """Update WS2812FX effects on main bar"""
        if self.ws2812fx.running and self.segments:
            self.ws2812fx.update()
            
            # Update LED colors from WS2812FX
            for i in range(self.num_leds):
                r, g, b = self.ws2812fx.leds[i]
                self.led_colors[i] = QColor(r, g, b)
            
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        led_width = self.width() / self.num_leds
        for i in range(self.num_leds):
            rect = QRectF(i * led_width, 0, led_width, self.height())
            if self.start_index is not None and self.end_index is not None:
                min_idx = min(self.start_index, self.end_index)
                max_idx = max(self.start_index, self.end_index)
                if min_idx <= i <= max_idx:
                    painter.setBrush(QColor('darkgray'))
                else:
                    painter.setBrush(self.led_colors[i])
            else:
                painter.setBrush(self.led_colors[i])
            painter.drawEllipse(rect.center(), led_width/2 - 2, self.height()/2 - 2)
        # Draw only the selected segment
        if self.selected_segment is not None and self.selected_segment < len(self.segments):
            seg = self.segments[self.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            start_x = start * led_width
            end_x = (end + 1) * led_width
            rect = QRectF(start_x, 0, end_x - start_x, self.height())
            painter.setPen(QPen(color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            led_width = self.width() / self.num_leds
            index = int(event.position().x() // led_width)
            self.start_index = index
            self.end_index = index
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_index is not None:
            led_width = self.width() / self.num_leds
            index = int(event.position().x() // led_width)
            self.end_index = index
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.start_index is not None:
            led_width = self.width() / self.num_leds
            index = int(event.position().x() // led_width)
            self.end_index = index
            if self.start_index > self.end_index:
                self.start_index, self.end_index = self.end_index, self.start_index
            # Create segment with defaults
            self.segments.append((self.start_index, self.end_index, QColor('red'), 'static', {}, 1000, False))
            self.selected_segment = len(self.segments) - 1
            self.start_index = None
            self.end_index = None
            self.parent_window.update_segment_config()
            self.parent_window.update_list()
            self.update_colors()

    

    def update_colors(self):
        # Clear WS2812FX segments
        self.ws2812fx.segments.clear()
        
        # Add all segments to WS2812FX
        for seg in self.segments:
            start, end, color, mode, signal_info, speed, reverse = seg
            # Convert QColor to RGB tuple
            rgb_color = (color.red(), color.green(), color.blue())
            
            # Convert mode string to WS2812FXMode enum
            try:
                ws2812fx_mode = getattr(WS2812FXMode, mode)
            except AttributeError:
                ws2812fx_mode = WS2812FXMode.STATIC
            
            # Add segment to WS2812FX
            self.ws2812fx.add_segment(
                start=start,
                stop=end,
                mode=ws2812fx_mode,
                colors=[rgb_color],  # Use single color for now
                speed=speed,
                reverse=reverse
            )
        
        # Start WS2812FX if we have segments
        if self.segments:
            self.ws2812fx.start()
        else:
            self.ws2812fx.stop()
            # Reset to gray if no segments
            self.led_colors = [QColor('gray')] * self.num_leds
        
        self.update()
        self.parent_window.update_list()


class MiniLEDPreview(QWidget):
    """Mini barre LED pour prévisualisation des effets WS2812FX"""

    def __init__(self, num_leds=100):
        super().__init__()
        self.num_leds = num_leds
        self.led_colors = [(0, 0, 0)] * num_leds  # Couleurs RGB
        self.ws2812fx = WS2812FX(num_leds)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_preview)
        self.setFixedHeight(20)
        self.setMinimumWidth(400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        led_width = self.width() / self.num_leds
        led_height = self.height()

        for i in range(self.num_leds):
            x = i * led_width
            y = 0

            # Couleur de la LED
            r, g, b = self.led_colors[i]
            color = QColor(r, g, b)

            # Dessiner la LED comme un carré contigu
            painter.setBrush(color)
            painter.setPen(QPen(color.darker(150), 1))
            painter.drawRect(int(x), int(y), int(led_width), int(led_height))

    def set_mode(self, mode: WS2812FXMode, colors=None, speed=1000, reverse=False):
        """Définit le mode d'effet à prévisualiser"""
        self.ws2812fx.segments.clear()

        # Couleurs par défaut si non spécifiées
        if colors is None:
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Rouge, Vert, Bleu

        # Ajouter le segment couvrant toute la mini barre
        self.ws2812fx.add_segment(
            start=0,
            stop=self.num_leds - 1,
            mode=mode,
            colors=colors,
            speed=speed,
            reverse=reverse
        )

        # Démarrer la prévisualisation
        self.start_preview()

    def set_mode_from_string(self, mode_str: str, color: QColor = None, speed: int = 1000, reverse: bool = False):
        """Définit le mode à partir d'une chaîne de caractères"""
        try:
            # Retirer le préfixe FX_MODE_ si présent
            if mode_str.startswith('FX_MODE_'):
                mode_name = mode_str[8:]  # Retirer "FX_MODE_"
            else:
                mode_name = mode_str

            # Convertir la chaîne en mode WS2812FX
            mode = getattr(WS2812FXMode, mode_name, WS2812FXMode.STATIC)

            # Convertir QColor en tuple RGB
            if color is None:
                colors = [(255, 0, 0), (0, 0, 0)]  # Rouge par défaut + noir pour arrière-plan
            else:
                colors = [(color.red(), color.green(), color.blue()), (0, 0, 0)]  # Couleur principale + noir pour arrière-plan

            self.set_mode(mode, colors, speed, reverse)
        except AttributeError:
            print(f"Mode inconnu: {mode_str}")
            # Mode par défaut
            self.set_mode(WS2812FXMode.STATIC, [(255, 0, 0)], speed, reverse)

    def set_speed(self, speed: int):
        """Modifie la vitesse de l'effet"""
        if self.ws2812fx.segments:
            segment = self.ws2812fx.segments[0]
            segment.speed = speed
            # Reset counters to ensure smooth transition
            segment.counter_mode_call = 0
            segment.counter_mode_step = 0
            segment.last_update_time = 0  # Reset timing
            self.update()  # Force visual update

    def set_reverse(self, reverse: bool):
        """Modifie le sens de l'effet"""
        if self.ws2812fx.segments:
            segment = self.ws2812fx.segments[0]
            segment.reverse = reverse
            # Reset counters to ensure smooth transition
            segment.counter_mode_call = 0
            segment.counter_mode_step = 0
            segment.last_update_time = 0  # Reset timing
            self.update()  # Force visual update

    def set_color(self, color: QColor):
        """Modifie la couleur de l'effet"""
        if self.ws2812fx.segments:
            self.ws2812fx.segments[0].colors = [(color.red(), color.green(), color.blue())]

    def start_preview(self):
        """Démarre la prévisualisation"""
        if not self.timer.isActive():
            self.ws2812fx.start()
            self.timer.start(50)  # ~20 FPS

    def stop_preview(self):
        """Arrête la prévisualisation"""
        if self.timer.isActive():
            self.timer.stop()
            self.ws2812fx.stop()
            # Remettre toutes les LEDs à noir
            self.led_colors = [(0, 0, 0)] * self.num_leds
            self.update()

    def update_preview(self):
        """Met à jour la prévisualisation"""
        self.ws2812fx.update()

        # Synchroniser les couleurs
        for i in range(self.num_leds):
            r, g, b = self.ws2812fx.leds[i]
            self.led_colors[i] = (r, g, b)

        self.update()


class SegmentConfigDialog(QDialog):
    def __init__(self, color, mode, signal_info, speed=1000, reverse=False, is_editing=False):
        super().__init__()
        self.setWindowTitle("Configurer le Segment")
        layout = QVBoxLayout()
        self.dbc_manager = DBCManager()
        self.color = color
        self.color_label = QLabel("Couleur actuelle:")
        self.color_label.setStyleSheet(f"background-color: {self.color.name()}; color: white; padding: 5px;")
        self.color_btn = QPushButton("Choisir Couleur")
        self.color_btn.clicked.connect(self.choose_color)

        # Mini LED Preview
        self.mini_preview = MiniLEDPreview(100)  # 100 LEDs for preview
        self.mini_preview.setFixedHeight(60)

        # Mode combo with all WS2812FX modes
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            'STATIC',
            'BLINK',
            'BREATH',
            'COLOR_WIPE',
            'COLOR_WIPE_INV',
            'COLOR_WIPE_REV',
            'COLOR_WIPE_REV_INV',
            'COLOR_WIPE_RANDOM',
            'RANDOM_COLOR',
            'SINGLE_DYNAMIC',
            'MULTI_DYNAMIC',
            'RAINBOW',
            'RAINBOW_CYCLE',
            'SCAN',
            'DUAL_SCAN',
            'FADE',
            'THEATER_CHASE',
            'THEATER_CHASE_RAINBOW',
            'RUNNING_LIGHTS',
            'TWINKLE',
            'TWINKLE_RANDOM',
            'TWINKLE_FADE',
            'TWINKLE_FADE_RANDOM',
            'SPARKLE',
            'FLASH_SPARKLE',
            'HYPER_SPARKLE',
            'STROBE',
            'STROBE_RAINBOW',
            'MULTI_STROBE',
            'BLINK_RAINBOW',
            'CHASE_WHITE',
            'CHASE_COLOR',
            'CHASE_RANDOM',
            'CHASE_RAINBOW',
            'CHASE_FLASH',
            'CHASE_FLASH_RANDOM',
            'CHASE_RAINBOW_WHITE',
            'CHASE_BLACKOUT',
            'CHASE_BLACKOUT_RAINBOW',
            'COLOR_SWEEP_RANDOM',
            'RUNNING_COLOR',
            'RUNNING_RED_BLUE',
            'RUNNING_RANDOM',
            'LARSON_SCANNER',
            'COMET',
            'FIREWORKS',
            'FIREWORKS_RANDOM',
            'MERRY_CHRISTMAS',
            'FIRE_FLICKER',
            'FIRE_FLICKER_SOFT',
            'FIRE_FLICKER_INTENSE',
            'CIRCUS_COMBUSTUS',
            'HALLOWEEN',
            'BICOLOR_CHASE',
            'TRICOLOR_CHASE',
            'ICU'
        ])
        self.mode_combo.setCurrentText(mode)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Speed control
        self.speed_label = QLabel("Vitesse:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(speed)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        self.speed_slider.sliderReleased.connect(self.on_speed_slider_released)

        # Reverse checkbox
        self.reverse_checkbox = QCheckBox("Inverser")
        self.reverse_checkbox.setChecked(reverse)
        self.reverse_checkbox.stateChanged.connect(self.on_reverse_changed)

        # Message combo
        self.message_combo = QComboBox()
        self.message_combo.addItems(self.dbc_manager.get_message_names())

        # Signal combo
        self.signal_combo = QComboBox()

        # Value combo (Active)
        self.active_value_combo = QComboBox()
        self.active_value_combo.setEnabled(False)

        # Inactive value combo
        self.inactive_value_combo = QComboBox()
        self.inactive_value_combo.setEnabled(False)

        # Connect signals after widgets are created
        self.message_combo.currentTextChanged.connect(self.on_message_changed)
        self.signal_combo.currentTextChanged.connect(self.on_signal_changed)

        # Initialize with current signal_info
        if signal_info and 'message' in signal_info:
            # Temporarily disconnect signals to avoid interference during initialization
            self.message_combo.currentTextChanged.disconnect(self.on_message_changed)
            self.signal_combo.currentTextChanged.disconnect(self.on_signal_changed)

            self.message_combo.setCurrentText(signal_info['message'])
            self.on_message_changed(signal_info['message'])
            if 'signal' in signal_info:
                self.signal_combo.setCurrentText(signal_info['signal'])
                self.on_signal_changed(signal_info['signal'])
                if 'active_value' in signal_info:
                    self.active_value_combo.setCurrentText(signal_info['active_value'])
                if 'inactive_value' in signal_info:
                    self.inactive_value_combo.setCurrentText(signal_info['inactive_value'])
                # Support legacy 'value' field for backward compatibility
                elif 'value' in signal_info:
                    self.active_value_combo.setCurrentText(signal_info['value'])

            # Reconnect signals
            self.message_combo.currentTextChanged.connect(self.on_message_changed)
            self.signal_combo.currentTextChanged.connect(self.on_signal_changed)

            # Force refresh of value combo in case signal change didn't trigger properly
            if 'signal' in signal_info:
                self.on_signal_changed(signal_info['signal'])

        # Layout
        layout.addWidget(QLabel("Aperçu:"))
        layout.addWidget(self.mini_preview)
        layout.addWidget(QLabel("Couleur:"))
        layout.addWidget(self.color_label)
        layout.addWidget(self.color_btn)
        layout.addWidget(QLabel("Mode:"))
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.speed_slider)
        layout.addWidget(self.reverse_checkbox)
        layout.addWidget(QLabel("Message CAN:"))
        layout.addWidget(self.message_combo)
        layout.addWidget(QLabel("Signal:"))
        layout.addWidget(self.signal_combo)
        layout.addWidget(QLabel("Valeur Active:"))
        layout.addWidget(self.active_value_combo)
        layout.addWidget(QLabel("Valeur Inactive:"))
        layout.addWidget(self.inactive_value_combo)

        self.delete_requested = False
        if is_editing:
            delete_btn = QPushButton("Supprimer le Segment")
            delete_btn.clicked.connect(self.delete_segment)
            layout.addWidget(delete_btn)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)

        # Initialize preview
        self.on_mode_changed(mode)

    def on_mode_changed(self, mode):
        # Update mini preview with selected mode
        self.mini_preview.set_mode_from_string(mode, self.color, self.speed_slider.value(), self.reverse_checkbox.isChecked())

    def on_speed_changed(self, speed):
        # Update preview speed (light update during slider movement)
        self.mini_preview.set_speed(speed)

    def on_speed_slider_released(self):
        # Full update when slider is released
        speed = self.speed_slider.value()
        self.mini_preview.set_speed(speed)
        # Force a complete refresh
        self.mini_preview.update()

    def on_reverse_changed(self, state):
        # Update preview reverse setting
        self.mini_preview.set_reverse(state == Qt.Checked)

    def on_message_changed(self, message_name):
        self.signal_combo.clear()
        if message_name:
            signals = self.dbc_manager.get_signals_for_message(message_name)
            self.signal_combo.addItems(signals)
        # Reset value combos without triggering on_signal_changed
        self.active_value_combo.clear()
        self.inactive_value_combo.clear()
        self.active_value_combo.setEnabled(False)
        self.inactive_value_combo.setEnabled(False)

    def on_signal_changed(self, signal_name):
        self.active_value_combo.clear()
        self.inactive_value_combo.clear()
        self.active_value_combo.setEnabled(False)
        self.inactive_value_combo.setEnabled(False)
        if signal_name:
            message_text = self.message_combo.currentText()
            if message_text:
                full_signal_name = f"{message_text}.{signal_name}"
                values = self.dbc_manager.get_signal_value_names(full_signal_name)
                if values:
                    self.active_value_combo.addItems(values)
                    self.inactive_value_combo.addItems(values)
                    self.active_value_combo.setEnabled(True)
                    self.inactive_value_combo.setEnabled(True)

    def choose_color(self):
        color = QColorDialog.getColor(self.color)
        if color.isValid():
            self.color = color
            self.color_label.setStyleSheet(f"background-color: {self.color.name()}; color: white; padding: 5px;")
            # Update preview color
            self.mini_preview.set_color(self.color)

    def delete_segment(self):
        self.delete_requested = True
        self.accept()

    def get_values(self):
        message = self.message_combo.currentText()
        signal = self.signal_combo.currentText()
        active_value = self.active_value_combo.currentText() if self.active_value_combo.isEnabled() else ""
        inactive_value = self.inactive_value_combo.currentText() if self.inactive_value_combo.isEnabled() else ""
        signal_info = {}
        if message and signal:
            signal_data = self.dbc_manager.get_signal_by_name(f"{message}.{signal}")
            if signal_data:
                # Convert choices to JSON serializable format
                choices_dict = {}
                if signal_data['choices']:
                    for key, named_value in signal_data['choices'].items():
                        # Ensure both key and value are strings
                        key_str = str(key)
                        # Handle NamedSignalValue objects properly
                        if hasattr(named_value, 'name'):
                            value_str = named_value.name
                        else:
                            value_str = str(named_value)
                        choices_dict[key_str] = value_str

                signal_info = {
                    'message': message,
                    'signal': signal,
                    'active_value': active_value,
                    'inactive_value': inactive_value,
                    'id': signal_data['message_id'],
                    'start': signal_data['start'],
                    'length': signal_data['length'],
                    'byte_order': signal_data['byte_order'],
                    'is_signed': signal_data['is_signed'],
                    'scale': signal_data['scale'],
                    'offset': signal_data['offset'],
                    'minimum': signal_data['minimum'],
                    'maximum': signal_data['maximum'],
                    'unit': signal_data['unit'],
                    'choices': choices_dict,
                    'comment': signal_data['comment']
                }
        return self.color, self.mode_combo.currentText(), signal_info, self.speed_slider.value(), self.reverse_checkbox.isChecked()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur de Barre LED")
        central = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        
        # Left widget
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        num_leds, segments = self.load_config()
        if not os.path.exists('segments.json'):
            num_leds, ok = QInputDialog.getInt(self, "Configurer la Barre", "Nombre de LEDs:", 16, 1, 10000)
            if ok:
                num_leds = num_leds
            else:
                num_leds = 16
        self.led_bar = LEDBar(num_leds, self)
        self.led_bar.segments = segments
        left_layout.addWidget(self.led_bar)
        menu_layout = QHBoxLayout()
        create_btn = QPushButton("Créer Segment (utilisez la souris sur la barre)")
        create_btn.setEnabled(False)
        menu_layout.addWidget(create_btn)
        left_layout.addLayout(menu_layout)
        self.segment_list = QListWidget()
        self.segment_list.itemSelectionChanged.connect(self.on_segment_selected)
        left_layout.addWidget(self.segment_list)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right widget - Configuration Panel
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Configuration du Segment"))
        
        # Mini LED Preview (moved to top)
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Aperçu:"))
        self.mini_preview_config = MiniLEDPreview(50)  # Smaller preview for config panel
        self.mini_preview_config.setFixedHeight(20)
        preview_layout.addWidget(self.mini_preview_config)
        right_layout.addLayout(preview_layout)
        
        # Segment name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nom:"))
        self.segment_name_edit = QLineEdit()
        self.segment_name_edit.setPlaceholderText("Nom du segment")
        self.segment_name_edit.textChanged.connect(self.on_segment_name_changed)
        self.segment_name_edit.setEnabled(False)
        name_layout.addWidget(self.segment_name_edit)
        right_layout.addLayout(name_layout)
        
        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Couleur:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(50, 30)
        self.color_btn.clicked.connect(self.on_color_changed)
        self.color_btn.setEnabled(False)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        right_layout.addLayout(color_layout)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo_config = QComboBox()
        self.mode_combo_config.addItems([
            'STATIC', 'BLINK', 'BREATH', 'COLOR_WIPE', 'COLOR_WIPE_INV', 'COLOR_WIPE_REV',
            'COLOR_WIPE_REV_INV', 'COLOR_WIPE_RANDOM', 'RANDOM_COLOR', 'SINGLE_DYNAMIC',
            'MULTI_DYNAMIC', 'RAINBOW', 'RAINBOW_CYCLE', 'SCAN', 'DUAL_SCAN', 'FADE',
            'THEATER_CHASE', 'THEATER_CHASE_RAINBOW', 'RUNNING_LIGHTS', 'TWINKLE',
            'TWINKLE_RANDOM', 'TWINKLE_FADE', 'TWINKLE_FADE_RANDOM', 'SPARKLE',
            'FLASH_SPARKLE', 'HYPER_SPARKLE', 'STROBE', 'STROBE_RAINBOW', 'MULTI_STROBE',
            'BLINK_RAINBOW', 'CHASE_WHITE', 'CHASE_COLOR', 'CHASE_RANDOM', 'CHASE_RAINBOW',
            'CHASE_FLASH', 'CHASE_FLASH_RANDOM', 'CHASE_RAINBOW_WHITE', 'CHASE_BLACKOUT',
            'CHASE_BLACKOUT_RAINBOW', 'COLOR_SWEEP_RANDOM', 'RUNNING_COLOR', 'RUNNING_RED_BLUE',
            'RUNNING_RANDOM', 'LARSON_SCANNER', 'COMET', 'FIREWORKS', 'FIREWORKS_RANDOM',
            'FIRE_FLICKER', 'FIRE_FLICKER_SOFT', 'FIRE_FLICKER_INTENSE', 'CIRCUS_COMBUSTUS',
            'HALLOWEEN', 'BICOLOR_CHASE', 'TRICOLOR_CHASE', 'ICU'
        ])
        self.mode_combo_config.currentTextChanged.connect(self.on_mode_config_changed)
        self.mode_combo_config.setEnabled(False)
        mode_layout.addWidget(self.mode_combo_config)
        right_layout.addLayout(mode_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Vitesse:"))
        self.speed_slider_config = QSlider(Qt.Horizontal)
        self.speed_slider_config.setRange(1, 1000)
        self.speed_slider_config.setValue(1000)
        self.speed_slider_config.valueChanged.connect(self.on_speed_config_changed)
        self.speed_slider_config.sliderReleased.connect(self.on_speed_config_released)
        self.speed_slider_config.setEnabled(False)
        speed_layout.addWidget(self.speed_slider_config)
        self.speed_label_config = QLabel("1000")
        self.speed_label_config.setFixedWidth(50)
        speed_layout.addWidget(self.speed_label_config)
        right_layout.addLayout(speed_layout)
        
        # Reverse checkbox
        self.reverse_checkbox_config = QCheckBox("Inverser")
        self.reverse_checkbox_config.stateChanged.connect(self.on_reverse_config_changed)
        self.reverse_checkbox_config.setEnabled(False)
        right_layout.addWidget(self.reverse_checkbox_config)
        
        # Add spacing before CAN section
        right_layout.addSpacing(10)
        
        # CAN Configuration section
        can_group = QGroupBox("Configuration CAN")
        can_layout = QVBoxLayout()
        
        # Message combo
        message_layout = QHBoxLayout()
        message_layout.addWidget(QLabel("Message:"))
        self.message_combo_config = QComboBox()
        self.message_combo_config.currentTextChanged.connect(self.on_message_config_changed)
        self.message_combo_config.setEnabled(False)
        message_layout.addWidget(self.message_combo_config)
        can_layout.addLayout(message_layout)
        
        # Signal combo
        signal_layout = QHBoxLayout()
        signal_layout.addWidget(QLabel("Signal:"))
        self.signal_combo_config = QComboBox()
        self.signal_combo_config.currentTextChanged.connect(self.on_signal_config_changed)
        self.signal_combo_config.setEnabled(False)
        signal_layout.addWidget(self.signal_combo_config)
        can_layout.addLayout(signal_layout)
        
        # Active value combo
        active_layout = QHBoxLayout()
        active_layout.addWidget(QLabel("Valeur Active:"))
        self.active_value_combo_config = QComboBox()
        self.active_value_combo_config.currentTextChanged.connect(self.on_active_value_config_changed)
        self.active_value_combo_config.setEnabled(False)
        active_layout.addWidget(self.active_value_combo_config)
        can_layout.addLayout(active_layout)
        
        # Inactive value combo
        inactive_layout = QHBoxLayout()
        inactive_layout.addWidget(QLabel("Valeur Inactive:"))
        self.inactive_value_combo_config = QComboBox()
        self.inactive_value_combo_config.currentTextChanged.connect(self.on_inactive_value_config_changed)
        self.inactive_value_combo_config.setEnabled(False)
        inactive_layout.addWidget(self.inactive_value_combo_config)
        can_layout.addLayout(inactive_layout)
        
        can_group.setLayout(can_layout)
        right_layout.addWidget(can_group)
        buttons_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.clicked.connect(self.on_apply_config)
        self.apply_btn.setEnabled(False)
        buttons_layout.addWidget(self.apply_btn)
        
        self.delete_btn = QPushButton("Supprimer")
        self.delete_btn.clicked.connect(self.on_delete_segment)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: red; }")
        buttons_layout.addWidget(self.delete_btn)
        
        right_layout.addLayout(buttons_layout)
        
        # Add stretch to push everything to the top
        right_layout.addStretch()
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(splitter)
        splitter.setSizes([800, 200])
        self.setCentralWidget(central)
        self.timer = QTimer()
        self.timer.timeout.connect(self.blink)
        self.timer.start(500)
        
        # Initialize CAN combos
        self.dbc_manager = DBCManager()
        self.message_combo_config.addItems(self.dbc_manager.get_message_names())
        
        self.update_list()
        self.led_bar.update_colors()

    def load_config(self):
        if os.path.exists('segments.json'):
            with open('segments.json', 'r') as f:
                data = json.load(f)
            num_leds = data.get('num_leds', 16)
            segments = []
            for seg_dict in data.get('segments', []):
                start = seg_dict['start']
                end = seg_dict['end']
                color = QColor(seg_dict['color'])
                mode = seg_dict['mode']
                signal_info = seg_dict.get('signal_info', {})
                speed = seg_dict.get('speed', 1000)  # Valeur par défaut
                reverse = seg_dict.get('reverse', False)  # Valeur par défaut
                segments.append((start, end, color, mode, signal_info, speed, reverse))
            return num_leds, segments
        return 16, []

    def save_config(self):
        segments_list = []
        for seg in self.led_bar.segments:
            start, end, color, mode, signal_info, speed, reverse = seg
            seg_dict = {'start': start, 'end': end, 'color': color.name(), 'mode': mode, 'signal_info': signal_info, 'speed': speed, 'reverse': reverse}
            segments_list.append(seg_dict)
        data = {'num_leds': self.led_bar.num_leds, 'segments': segments_list}
        with open('segments.json', 'w') as f:
            json.dump(data, f, indent=4)

    def on_segment_selected(self):
        selected_items = self.segment_list.selectedItems()
        if selected_items:
            index = self.segment_list.row(selected_items[0])
            if index < len(self.led_bar.segments):
                if index != self.led_bar.selected_segment:
                    self.led_bar.selected_segment = index
                    self.led_bar.update_colors()
                    self.update_segment_config()
        else:
            if self.led_bar.selected_segment is not None:
                self.led_bar.selected_segment = None
                self.led_bar.update_colors()
                self.update_segment_config()

    def on_code_selected(self, item):
        selected_text = item.text()
        for i, seg in enumerate(self.led_bar.segments):
            start, end, color, mode, signal_info, speed, reverse = seg
            if signal_info:
                # Check new active/inactive values
                if ('active_value' in signal_info and signal_info['active_value'] == selected_text) or \
                   ('inactive_value' in signal_info and signal_info['inactive_value'] == selected_text):
                    self.led_bar.selected_segment = i
                    self.led_bar.update_colors()
                    self.segment_list.setCurrentRow(i)
                    break
                # Check legacy single value
                elif 'value' in signal_info and signal_info['value'] == selected_text:
                    self.led_bar.selected_segment = i
                    self.led_bar.update_colors()
                    self.segment_list.setCurrentRow(i)
                    break
                elif 'signal' in signal_info:
                    signal_text = f"{signal_info.get('message', '')}.{signal_info.get('signal', '')}"
                    if signal_text == selected_text:
                        self.led_bar.selected_segment = i
                        self.led_bar.update_colors()
                        self.segment_list.setCurrentRow(i)
                        break

    def update_list(self):
        if not hasattr(self, 'segment_list'):
            return
        self.segment_list.itemSelectionChanged.disconnect(self.on_segment_selected)
        self.segment_list.clear()
        for i, seg in enumerate(self.led_bar.segments):
            start, end, color, mode, signal_info, speed, reverse = seg

            if signal_info:
                # Récupérer les informations CAN
                can_id = signal_info.get('id', 'N/A')
                message = signal_info.get('message', 'N/A')
                signal = signal_info.get('signal', 'N/A')

                # Formater l'ID CAN avec son label
                can_info = f"ID {can_id} ({message})"

                # Récupérer les valeurs active/inactive
                active_val = signal_info.get('active_value', '')
                inactive_val = signal_info.get('inactive_value', '')

                # Créer l'affichage des valeurs
                if active_val and inactive_val:
                    values_info = f"Actif: {active_val} | Inactif: {inactive_val}"
                elif active_val:
                    values_info = f"Actif: {active_val}"
                elif inactive_val:
                    values_info = f"Inactif: {inactive_val}"
                else:
                    values_info = "Aucune valeur"

                # Get segment name
                segment_name = signal_info.get('name', f"Segment {i+1}")

                # Affichage simplifié - uniquement le nom
                display_text = segment_name
            else:
                # Get segment name for segments without CAN info
                segment_name = signal_info.get('name', f"Segment {i+1}") if signal_info else f"Segment {i+1}"
                # Affichage simplifié - uniquement le nom
                display_text = segment_name

            item = QListWidgetItem(display_text)
            self.segment_list.addItem(item)

        self.segment_list.itemSelectionChanged.connect(self.on_segment_selected)
        current = self.segment_list.currentRow()
        if self.led_bar.selected_segment is not None and self.led_bar.selected_segment < len(self.led_bar.segments) and current != self.led_bar.selected_segment:
            self.segment_list.setCurrentRow(self.led_bar.selected_segment)

    def blink(self):
        if self.led_bar.selected_segment is not None and self.led_bar.selected_segment < len(self.led_bar.segments):
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            if seg[3] == 'blinking':
                start, end = seg[0], seg[1]
                for i in range(start, end + 1):
                    if self.led_bar.led_colors[i] == seg[2]:
                        self.led_bar.led_colors[i] = QColor('gray')
                    else:
                        self.led_bar.led_colors[i] = seg[2]
        self.led_bar.update()

    def update_segment_config(self):
        """Met à jour l'interface de configuration avec les données du segment sélectionné"""
        if self.led_bar.selected_segment is not None and self.led_bar.selected_segment < len(self.led_bar.segments):
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            
            # Update segment name
            segment_name = signal_info.get('name', '') if signal_info else ''
            if not segment_name:
                segment_name = f"Segment {self.led_bar.selected_segment + 1}"
            self.segment_name_edit.setText(segment_name)
            self.segment_name_edit.setEnabled(True)
            
            # Update color button
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
            self.color_btn.setEnabled(True)
            
            # Update mode
            self.mode_combo_config.setCurrentText(mode)
            self.mode_combo_config.setEnabled(True)
            
            # Update speed
            self.speed_slider_config.setValue(speed)
            self.speed_label_config.setText(str(speed))
            self.speed_slider_config.setEnabled(True)
            
            # Update reverse
            self.reverse_checkbox_config.setChecked(reverse)
            self.reverse_checkbox_config.setEnabled(True)
            
            # Update preview
            self.mini_preview_config.set_mode_from_string(mode, color, speed, reverse)
            
            # Update CAN configuration
            if signal_info and 'message' in signal_info:
                # Temporarily disconnect signals to avoid interference during initialization
                self.message_combo_config.currentTextChanged.disconnect(self.on_message_config_changed)
                self.signal_combo_config.currentTextChanged.disconnect(self.on_signal_config_changed)
                
                self.message_combo_config.setCurrentText(signal_info['message'])
                self.on_message_config_changed(signal_info['message'])
                if 'signal' in signal_info:
                    self.signal_combo_config.setCurrentText(signal_info['signal'])
                    self.on_signal_config_changed(signal_info['signal'])
                    if 'active_value' in signal_info:
                        self.active_value_combo_config.setCurrentText(signal_info['active_value'])
                    if 'inactive_value' in signal_info:
                        self.inactive_value_combo_config.setCurrentText(signal_info['inactive_value'])
                    # Support legacy 'value' field for backward compatibility
                    elif 'value' in signal_info:
                        self.active_value_combo_config.setCurrentText(signal_info['value'])
                
                # Reconnect signals
                self.message_combo_config.currentTextChanged.connect(self.on_message_config_changed)
                self.signal_combo_config.currentTextChanged.connect(self.on_signal_config_changed)
                
                self.message_combo_config.setEnabled(True)
                self.signal_combo_config.setEnabled(True)
                self.active_value_combo_config.setEnabled(True)
                self.inactive_value_combo_config.setEnabled(True)
            else:
                self.message_combo_config.setCurrentText("")
                self.signal_combo_config.clear()
                self.active_value_combo_config.clear()
                self.inactive_value_combo_config.clear()
                self.message_combo_config.setEnabled(True)
                self.signal_combo_config.setEnabled(False)
                self.active_value_combo_config.setEnabled(False)
                self.inactive_value_combo_config.setEnabled(False)
            
            # Enable buttons
            self.apply_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            # No segment selected
            self.segment_name_edit.clear()
            self.segment_name_edit.setEnabled(False)
            self.color_btn.setStyleSheet("")
            self.color_btn.setEnabled(False)
            self.mode_combo_config.setEnabled(False)
            self.speed_slider_config.setEnabled(False)
            self.reverse_checkbox_config.setEnabled(False)
            self.message_combo_config.setEnabled(False)
            self.signal_combo_config.setEnabled(False)
            self.active_value_combo_config.setEnabled(False)
            self.inactive_value_combo_config.setEnabled(False)
            self.apply_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
            # Stop preview when no segment selected
            self.mini_preview_config.stop_preview()

    def on_segment_name_changed(self, name):
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            if signal_info is None:
                signal_info = {}
            signal_info['name'] = name
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.update_list()
            self.led_bar.update_colors()

    def on_color_changed(self):
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            current_color = seg[2]
            
            color = QColorDialog.getColor(current_color, self, "Choisir la couleur")
            if color.isValid():
                self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
                # Apply immediately
                start, end, _, mode, signal_info, speed, reverse = seg
                self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
                self.led_bar.update_colors()
                self.update_list()
                # Update preview color
                self.mini_preview_config.set_color(color)

    def on_mode_config_changed(self, mode):
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, _, signal_info, speed, reverse = seg
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.led_bar.update_colors()
            # Update preview
            self.mini_preview_config.set_mode_from_string(mode, color, speed, reverse)

    def on_speed_config_changed(self, speed):
        self.speed_label_config.setText(str(speed))

    def on_speed_config_released(self):
        if self.led_bar.selected_segment is not None:
            speed = self.speed_slider_config.value()
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, _, reverse = seg
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.led_bar.update_colors()
            # Update preview speed
            self.mini_preview_config.set_speed(speed)

    def on_reverse_config_changed(self, state):
        if self.led_bar.selected_segment is not None:
            reverse = state == Qt.Checked
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, _ = seg
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.led_bar.update_colors()
            # Update preview reverse
            self.mini_preview_config.set_reverse(reverse)

    def on_message_config_changed(self, message_name):
        self.signal_combo_config.clear()
        self.active_value_combo_config.clear()
        self.inactive_value_combo_config.clear()
        self.active_value_combo_config.setEnabled(False)
        self.inactive_value_combo_config.setEnabled(False)
        if message_name:
            signals = self.dbc_manager.get_signals_for_message(message_name)
            self.signal_combo_config.addItems(signals)
        self.signal_combo_config.setEnabled(bool(message_name))
        
        # Update signal_info
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            if message_name:
                signal_info = signal_info.copy() if signal_info else {}
                signal_info['message'] = message_name
                # Clear signal and values when message changes
                if 'signal' in signal_info:
                    del signal_info['signal']
                if 'active_value' in signal_info:
                    del signal_info['active_value']
                if 'inactive_value' in signal_info:
                    del signal_info['inactive_value']
            else:
                signal_info = {}
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.update_list()
            self.led_bar.update_colors()

    def on_signal_config_changed(self, signal_name):
        self.active_value_combo_config.clear()
        self.inactive_value_combo_config.clear()
        self.active_value_combo_config.setEnabled(False)
        self.inactive_value_combo_config.setEnabled(False)
        if signal_name:
            message_text = self.message_combo_config.currentText()
            if message_text:
                full_signal_name = f"{message_text}.{signal_name}"
                values = self.dbc_manager.get_signal_value_names(full_signal_name)
                if values:
                    self.active_value_combo_config.addItems(values)
                    self.inactive_value_combo_config.addItems(values)
                    self.active_value_combo_config.setEnabled(True)
                    self.inactive_value_combo_config.setEnabled(True)
        
        # Update signal_info
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            if signal_name:
                signal_info = signal_info.copy() if signal_info else {}
                signal_info['signal'] = signal_name
                # Clear values when signal changes
                if 'active_value' in signal_info:
                    del signal_info['active_value']
                if 'inactive_value' in signal_info:
                    del signal_info['inactive_value']
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.update_list()
            self.led_bar.update_colors()

    def on_active_value_config_changed(self, value):
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            signal_info = signal_info.copy() if signal_info else {}
            signal_info['active_value'] = value
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.update_list()
            self.led_bar.update_colors()

    def on_inactive_value_config_changed(self, value):
        if self.led_bar.selected_segment is not None:
            seg = self.led_bar.segments[self.led_bar.selected_segment]
            start, end, color, mode, signal_info, speed, reverse = seg
            signal_info = signal_info.copy() if signal_info else {}
            signal_info['inactive_value'] = value
            self.led_bar.segments[self.led_bar.selected_segment] = (start, end, color, mode, signal_info, speed, reverse)
            self.update_list()
            self.led_bar.update_colors()

    def on_apply_config(self):
        # Save configuration to file
        self.save_config()

    def on_delete_segment(self):
        if self.led_bar.selected_segment is not None:
            reply = QMessageBox.question(self, "Confirmer la suppression", 
                                       "Êtes-vous sûr de vouloir supprimer ce segment ?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.led_bar.segments.pop(self.led_bar.selected_segment)
                self.led_bar.selected_segment = None
                self.led_bar.update_colors()
                self.update_list()
                self.update_segment_config()
                self.save_config()

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
