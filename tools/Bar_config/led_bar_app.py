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
            start, end, color, mode, signal_info = seg
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
        elif event.button() == Qt.RightButton:
            led_width = self.width() / self.num_leds
            index = int(event.position().x() // led_width)
            for i, seg in enumerate(self.segments):
                if seg[0] <= index <= seg[1]:
                    self.is_editing = True
                    self.selected_segment = i
                    self.show_config()
                    break

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
            self.segments.append((self.start_index, self.end_index, QColor('red'), 'static', {}))
            self.selected_segment = len(self.segments) - 1
            self.show_config()
            self.start_index = None
            self.end_index = None

    def show_config(self):
        if self.selected_segment is not None:
            seg = self.segments[self.selected_segment]
            dialog = SegmentConfigDialog(seg[2], seg[3], seg[4], self.is_editing)
            if dialog.exec():
                color, mode, code = dialog.get_values()
                if dialog.delete_requested:
                    self.segments.pop(self.selected_segment)
                    self.selected_segment = None
                else:
                    self.segments[self.selected_segment] = (seg[0], seg[1], color, mode, code)
                self.update_colors()
                # Hide after config only for new segments
                if not self.is_editing:
                    self.selected_segment = None
                    self.update()
            else:
                # Cancel pressed
                if not self.is_editing:
                    self.segments.pop()
                    self.selected_segment = None
                    self.update_colors()
        self.is_editing = False
        self.parent_window.save_config()

    def update_colors(self):
        self.led_colors = [QColor('gray')] * self.num_leds
        if self.selected_segment is not None and self.selected_segment < len(self.segments):
            seg = self.segments[self.selected_segment]
            start, end, color, mode, signal_info = seg
            for i in range(start, end + 1):
                self.led_colors[i] = color
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
        self.setFixedHeight(30)
        self.setMinimumWidth(400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        led_width = self.width() / self.num_leds
        led_height = self.height() - 4

        for i in range(self.num_leds):
            x = i * led_width
            y = 2

            # Couleur de la LED
            r, g, b = self.led_colors[i]
            color = QColor(r, g, b)

            # Dessiner la LED
            painter.setBrush(color)
            painter.setPen(QPen(color.darker(150), 1))
            painter.drawEllipse(x + 1, y, led_width - 2, led_height)

            # Ajouter un effet de brillance
            if r + g + b > 100:  # Si la LED est allumée
                highlight_color = QColor(255, 255, 255, 100)
                painter.setBrush(highlight_color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(x + led_width * 0.2, y + led_height * 0.2,
                                  led_width * 0.4, led_height * 0.4)

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
            self.ws2812fx.segments[0].speed = speed

    def set_reverse(self, reverse: bool):
        """Modifie le sens de l'effet"""
        if self.ws2812fx.segments:
            self.ws2812fx.segments[0].reverse = reverse

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
    def __init__(self, color, mode, signal_info, is_editing=False):
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
            'ICU',
            'CUSTOM_0',
            'CUSTOM_1',
            'CUSTOM_2',
            'CUSTOM_3',
            'CUSTOM_4',
            'CUSTOM_5',
            'CUSTOM_6',
            'CUSTOM_7',
            'CUSTOM_8',
            'CUSTOM_9',
            'CUSTOM_10',
            'CUSTOM_11',
            'CUSTOM_12',
            'CUSTOM_13',
            'CUSTOM_14',
            'CUSTOM_15',
            'CUSTOM_16',
            'CUSTOM_17',
            'CUSTOM_18',
            'CUSTOM_19',
            'CUSTOM_20',
            'CUSTOM_21',
            'CUSTOM_22',
            'CUSTOM_23',
            'CUSTOM_24',
            'CUSTOM_25',
            'CUSTOM_26',
            'CUSTOM_27',
            'CUSTOM_28',
            'CUSTOM_29',
            'CUSTOM_30',
            'CUSTOM_31',
            'CUSTOM_32',
            'CUSTOM_33',
            'CUSTOM_34',
            'CUSTOM_35',
            'CUSTOM_36',
            'CUSTOM_37',
            'CUSTOM_38',
            'CUSTOM_39',
            'CUSTOM_40',
            'CUSTOM_41',
            'CUSTOM_42',
            'CUSTOM_43',
            'CUSTOM_44',
            'CUSTOM_45',
            'CUSTOM_46',
            'CUSTOM_47',
            'CUSTOM_48',
            'CUSTOM_49'
        ])
        self.mode_combo.setCurrentText(mode)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Speed control
        self.speed_label = QLabel("Vitesse:")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 1000)
        self.speed_slider.setValue(1000)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)

        # Reverse checkbox
        self.reverse_checkbox = QCheckBox("Inverser")
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
        # Update preview speed
        self.mini_preview.set_speed(speed)

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
        return self.color, self.mode_combo.currentText(), signal_info

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
        self.config_btn = QPushButton("Configurer Segment")
        self.config_btn.clicked.connect(self.on_config_btn_clicked)
        left_layout.addWidget(self.config_btn)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Right widget
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Codes"))
        self.codes_list = QListWidget()
        self.codes_list.itemClicked.connect(self.on_code_selected)
        right_layout.addWidget(self.codes_list)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        central.setLayout(QVBoxLayout())
        central.layout().addWidget(splitter)
        splitter.setSizes([800, 200])
        self.setCentralWidget(central)
        self.timer = QTimer()
        self.timer.timeout.connect(self.blink)
        self.timer.start(500)
        self.update_list()

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
                segments.append((start, end, color, mode, signal_info))
            return num_leds, segments
        return 16, []

    def save_config(self):
        segments_list = []
        for seg in self.led_bar.segments:
            start, end, color, mode, signal_info = seg
            seg_dict = {'start': start, 'end': end, 'color': color.name(), 'mode': mode, 'signal_info': signal_info}
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
        else:
            if self.led_bar.selected_segment is not None:
                self.led_bar.selected_segment = None
                self.led_bar.update()

    def on_config_btn_clicked(self):
        selected_items = self.segment_list.selectedItems()
        if selected_items:
            index = self.segment_list.row(selected_items[0])
            if index < len(self.led_bar.segments):
                self.led_bar.is_editing = True
                self.led_bar.selected_segment = index
                self.led_bar.show_config()
        else:
            QMessageBox.information(self, "Aucune sélection", "Veuillez sélectionner un segment dans la liste.")

    def on_code_selected(self, item):
        selected_text = item.text()
        for i, seg in enumerate(self.led_bar.segments):
            start, end, color, mode, signal_info = seg
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
        self.segment_list.itemSelectionChanged.disconnect(self.on_segment_selected)
        self.codes_list.itemClicked.disconnect(self.on_code_selected)
        self.segment_list.clear()
        self.codes_list.clear()
        for i, seg in enumerate(self.led_bar.segments):
            start, end, color, mode, signal_info = seg

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

                # Affichage complet
                display_text = f"Segment {i+1}: LEDs {start}-{end} | {can_info} | Signal: {signal} | {values_info} | Mode: {mode}"
            else:
                display_text = f"Segment {i+1}: LEDs {start}-{end}, Mode: {mode}, Aucun signal"

            item = QListWidgetItem(display_text)
            self.segment_list.addItem(item)

            # Add individual values to codes list
            if signal_info:
                if 'active_value' in signal_info and signal_info['active_value']:
                    code_item = QListWidgetItem(f"Actif: {signal_info['active_value']}")
                    self.codes_list.addItem(code_item)
                if 'inactive_value' in signal_info and signal_info['inactive_value']:
                    code_item = QListWidgetItem(f"Inactif: {signal_info['inactive_value']}")
                    self.codes_list.addItem(code_item)
                # Legacy support
                elif 'value' in signal_info and signal_info['value']:
                    code_item = QListWidgetItem(signal_info['value'])
                    self.codes_list.addItem(code_item)

        self.segment_list.itemSelectionChanged.connect(self.on_segment_selected)
        self.codes_list.itemClicked.connect(self.on_code_selected)
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

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()
