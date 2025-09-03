import sys
import requests
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QWidget, QTreeWidget, QTreeWidgetItem,
                              QTextEdit, QSplitter, QMessageBox, QLineEdit, QLabel)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import QCheckBox, QPushButton


@dataclass
class CANSignal:
    """Structure pour stocker les informations d'un signal CAN"""
    name: str
    start_bit: int
    length: int
    byte_order: str  # 'big_endian' ou 'little_endian'
    value_type: str  # 'signed' ou 'unsigned'
    factor: float
    offset: float
    minimum: Optional[float]
    maximum: Optional[float]
    unit: str
    receivers: List[str] = field(default_factory=list)
    comment: str = ""
    values: Optional[Dict[int, str]] = None  # Ajout pour stocker les valeurs VAL_


@dataclass
class CANMessage:
    """Structure pour stocker les informations d'un message CAN"""
    id: int
    name: str
    size: int
    transmitter: str
    signals: List[CANSignal] = field(default_factory=list)
    comment: str = ""
    category: str = "Uncategorized"


class DBCParser:
    """Parseur pour les fichiers DBC"""
    
    def __init__(self):
        self.messages: Dict[int, CANMessage] = {}
        self.categories: Dict[str, List[CANMessage]] = {}
    
    def parse_dbc_content(self, content: str) -> None:
        """Parse le contenu d'un fichier DBC"""
        lines = content.split('\n')
        current_message = None
        val_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Parse les messages CAN
            if line.startswith('BO_'):
                current_message = self._parse_message(line)
                if current_message:
                    self.messages[current_message.id] = current_message
            
            # Parse les signaux
            elif line.startswith('SG_') and current_message:
                signal = self._parse_signal(line)
                if signal:
                    current_message.signals.append(signal)
            
            # Parse les commentaires de messages
            elif line.startswith('CM_ BO_'):
                self._parse_message_comment(line)
            
            # Parse les commentaires de signaux
            elif line.startswith('CM_ SG_'):
                self._parse_signal_comment(line)
            
            # Parse les valeurs des signaux
            elif line.startswith('VAL_'):
                val_lines.append(line)
        
        self._parse_val_lines(val_lines)
        self._categorize_messages()
    
    def _parse_message(self, line: str) -> Optional[CANMessage]:
        """Parse une ligne de définition de message"""
        # Format: BO_ <ID> <n>: <Size> <Transmitter>
        pattern = r'BO_\s+(\d+)\s+([^:]+):\s+(\d+)\s+(.+)'
        match = re.match(pattern, line)
        
        if match:
            msg_id = int(match.group(1))
            name = match.group(2).strip()
            size = int(match.group(3))
            transmitter = match.group(4).strip()
            
            return CANMessage(
                id=msg_id,
                name=name,
                size=size,
                transmitter=transmitter
            )
        return None
    
    def _parse_signal(self, line: str) -> Optional[CANSignal]:
        """Parse une ligne de définition de signal"""
        # Format complexe du signal DBC
        pattern = r'SG_\s+([^:]+):\s*(\d+)\|(\d+)@([01])([+-])\s*\(([^,]+),([^)]+)\)\s*\[([^|]*)\|([^\]]*)\]\s*"([^"]*)"\s*(.+)'
        match = re.match(pattern, line)
        
        if match:
            name = match.group(1).strip()
            start_bit = int(match.group(2))
            length = int(match.group(3))
            byte_order = 'big_endian' if match.group(4) == '0' else 'little_endian'
            value_type = 'signed' if match.group(5) == '-' else 'unsigned'
            factor = float(match.group(6))
            offset = float(match.group(7))
            minimum = float(match.group(8)) if match.group(8) else None
            maximum = float(match.group(9)) if match.group(9) else None
            unit = match.group(10)
            receivers = [r.strip() for r in match.group(11).split(',') if r.strip()]
            
            return CANSignal(
                name=name,
                start_bit=start_bit,
                length=length,
                byte_order=byte_order,
                value_type=value_type,
                factor=factor,
                offset=offset,
                minimum=minimum,
                maximum=maximum,
                unit=unit,
                receivers=receivers
            )
        return None
    
    def _parse_message_comment(self, line: str) -> None:
        """Parse les commentaires de messages"""
        pattern = r'CM_\s+BO_\s+(\d+)\s+"([^"]*)"'
        match = re.match(pattern, line)
        
        if match:
            msg_id = int(match.group(1))
            comment = match.group(2)
            
            if msg_id in self.messages:
                self.messages[msg_id].comment = comment
    
    def _parse_signal_comment(self, line: str) -> None:
        """Parse les commentaires de signaux"""
        pattern = r'CM_\s+SG_\s+(\d+)\s+([^"]+)\s+"([^"]*)"'
        match = re.match(pattern, line)
        
        if match:
            msg_id = int(match.group(1))
            signal_name = match.group(2).strip()
            comment = match.group(3)
            
            if msg_id in self.messages:
                for signal in self.messages[msg_id].signals:
                    if signal.name == signal_name:
                        signal.comment = comment
                        break
    
    def _parse_val_lines(self, val_lines: List[str]) -> None:
        """Parse les lignes VAL_ pour les valeurs des signaux"""
        for line in val_lines:
            # Format: VAL_ <msg_id> <signal_name> <val> "<desc>" ... ;
            pattern = r'VAL_\s+(\d+)\s+([A-Za-z0-9_]+)\s+(.*);'
            match = re.match(pattern, line)
            if not match:
                continue
            msg_id = int(match.group(1))
            signal_name = match.group(2)
            rest = match.group(3)
            # Extraire les couples valeur/description
            val_pattern = r'(\d+)\s+"([^"]+)"'
            values = dict(re.findall(val_pattern, rest))
            values = {int(k): v for k, v in values.items()}
            if msg_id in self.messages:
                for signal in self.messages[msg_id].signals:
                    if signal.name == signal_name:
                        signal.values = values
                        break
    
    def _is_human_readable_name(self, name: str) -> bool:
        """Determine if a message name is human readable"""
        # Filter overly technical or cryptic names
        
        # Check if name starts with ID followed by hex digits
        if name.upper().startswith('ID'):
            remaining = name[2:]
            if remaining and all(c in '0123456789ABCDEF' for c in remaining.upper()):
                return False
        
        # Check if it's only hexadecimal characters (3+ chars)
        if len(name) >= 3 and all(c in '0123456789ABCDEF' for c in name.upper()):
            return False
        
        # Check if it's a very long uppercase/digits/underscore name
        if len(name) >= 10 and all(c.isupper() or c.isdigit() or c == '_' for c in name):
            return False
        
        # Check short patterns with underscores (like AB_CD_EF)
        parts = name.split('_')
        if len(parts) == 3 and all(len(part) <= 3 for part in parts):
            return False
        
        # Generic diagnostic messages
        if name.upper().startswith('DI_'):
            return False
        
        # Generic TPMS messages with numbers
        if name.upper().startswith('TPMS_') and any(c.isdigit() for c in name):
            return False
        
        # Debug or test messages
        name_lower = name.lower()
        if '_debug' in name_lower or '_test' in name_lower:
            return False
        
        # Check that name contains at least some meaningful content
        alpha_chars = [c for c in name if c.isalpha()]
        if len(alpha_chars) < 3:  # At least 3 alphabetic characters
            return False
        
        # Look for meaningful words (longer than 2 characters)
        words = []
        current_word = ""
        for c in name:
            if c.isalpha():
                current_word += c
            else:
                if len(current_word) > 2:
                    words.append(current_word)
                current_word = ""
        if len(current_word) > 2:
            words.append(current_word)
        
        # At least one meaningful word or reasonable total length
        return len(words) > 0 or len(name) < 15
    
    def _categorize_messages(self) -> None:
        """Catégorise les messages selon leur nom"""
        categories = {
            "Body Control": ["BCM", "Body", "Door", "Window", "Light", "HVAC", "Climate", "Seat", "Mirror"],
            "Powertrain": ["Motor", "Battery", "Inverter", "Charge", "Power", "Energy", "Thermal", "Drive", "Regen"],
            "Chassis": ["Brake", "ABS", "ESP", "Steering", "Wheel", "Suspension", "Tire", "Stability"],
            "Infotainment": ["UI", "Display", "Audio", "Media", "Navigation", "Phone", "Screen"],
            "Autopilot": ["AP", "Autopilot", "Camera", "Radar", "Vision", "Lane", "Speed", "Assist", "Safety"],
            "Vehicle Status": ["Status", "State", "Info", "Diagnostic", "Error", "Warning", "Alert", "Vehicle"],
            "Communication": ["Gateway", "Network", "CAN", "LIN", "Ethernet"]
        }
        
        # Filter first for messages with readable names
        readable_messages = {}
        for msg_id, msg in self.messages.items():
            if self._is_human_readable_name(msg.name):
                readable_messages[msg_id] = msg
        
        for message in readable_messages.values():
            message.category = "Uncategorized"
            
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword.lower() in message.name.lower():
                        message.category = category
                        break
                if message.category != "Uncategorized":
                    break
        
        # Organize by categories (only readable messages)
        self.categories = {}
        for message in readable_messages.values():
            if message.category not in self.categories:
                self.categories[message.category] = []
            self.categories[message.category].append(message)
        
        # Update messages dict to keep only readable ones
        self.messages = readable_messages


class LoaderThread(QThread):
    """Thread pour charger le fichier DBC de manière asynchrone"""
    finished = Signal(object)  # Émet le parser une fois terminé
    error = Signal(str)
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            
            parser = DBCParser()
            parser.parse_dbc_content(response.text)
            
            self.finished.emit(parser)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.parser = None
        self.setWindowTitle("Analyseur DBC Tesla Model 3")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_dbc_file()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Splitter pour diviser la vue
        splitter = QSplitter(Qt.Horizontal)
        
        # Côté gauche : Arbre + Recherche
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Arbre des catégories et messages
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Catégories et Messages CAN")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.currentItemChanged.connect(self.on_current_item_changed)
        self.tree_widget.setFocus()  # Pour que les touches fléchées fonctionnent dès le départ
        
        # Zone de recherche
        search_label = QLabel("Recherche:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tapez le nom d'un signal/champ...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.on_search_enter)
        
        # Ajouter à la mise en page gauche
        left_layout.addWidget(self.tree_widget)
        left_layout.addWidget(search_label)
        left_layout.addWidget(self.search_input)
        
        self.export_button = QPushButton("Exporter sélection JSON")
        self.export_button.clicked.connect(self.export_selected_to_json)
        left_layout.addWidget(self.export_button)
        
        # Zone d'informations (côté droit)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlainText("Chargement du fichier DBC en cours...")
        
        splitter.addWidget(left_widget)
        splitter.addWidget(self.info_text)
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # Variables pour la recherche
        self.all_message_items = []  # Liste de tous les éléments de message pour la recherche
        self.current_search_results = []  # Résultats de recherche actuels
        self.current_search_index = 0  # Index dans les résultats de recherche
        
        layout.addWidget(splitter)
        
        # Barre de statut
        self.statusBar().showMessage("Initialisation...")
        
        self.message_checkboxes = {}  # msg_id: QCheckBox
    
    def load_dbc_file(self):
        """Charge le fichier DBC depuis l'URL"""
        url = "https://raw.githubusercontent.com/joshwardell/model3dbc/refs/heads/master/Model3CAN.dbc"
        
        self.loader_thread = LoaderThread(url)
        self.loader_thread.finished.connect(self.on_dbc_loaded)
        self.loader_thread.error.connect(self.on_load_error)
        self.loader_thread.start()
    
    def on_dbc_loaded(self, parser: DBCParser):
        """Callback appelé quand le fichier DBC est chargé"""
        self.parser = parser
        self.populate_tree()
        self.statusBar().showMessage(f"Fichier DBC chargé: {len(parser.messages)} messages, {len(parser.categories)} catégories")
        
        # Message de bienvenue
        welcome_text = f"""
Analyseur DBC Tesla Model 3 - Fichier chargé avec succès !

Statistiques:
- {len(parser.messages)} messages CAN lisibles
- {len(parser.categories)} catégories
- {sum(len(msg.signals) for msg in parser.messages.values())} signaux au total

Instructions:
- Parcourez les catégories dans l'arbre à gauche
- Double-cliquez sur un message pour voir ses détails
- Les informations s'affichent dans cette zone

Catégories disponibles:
"""
        for category, messages in parser.categories.items():
            welcome_text += f"- {category}: {len(messages)} messages\n"
        
        self.info_text.setPlainText(welcome_text)
    
    def on_load_error(self, error_msg: str):
        """Callback appelé en cas d'erreur de chargement"""
        self.statusBar().showMessage("Erreur de chargement")
        self.info_text.setPlainText(f"Erreur lors du chargement du fichier DBC:\n{error_msg}")
        
        QMessageBox.critical(self, "Erreur", f"Impossible de charger le fichier DBC:\n{error_msg}")
    
    def populate_tree(self):
        self.tree_widget.clear()
        self.all_signal_items = []  # Liste de tous les éléments de signal pour la recherche
        self.signal_checkboxes = {}  # (msg_id, signal_name): QCheckBox
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Sélection", "Catégories et Messages CAN"])
        for category, messages in sorted(self.parser.categories.items()):
            category_item = QTreeWidgetItem(self.tree_widget)
            category_item.setText(1, f"{category} ({len(messages)})")
            category_item.setData(0, Qt.UserRole, {"type": "category", "data": category})
            for message in sorted(messages, key=lambda m: m.name):
                message_item = QTreeWidgetItem(category_item)
                message_item.setText(1, f"{message.name} (ID: 0x{message.id:X})")
                message_item.setData(0, Qt.UserRole, {"type": "message", "data": message})
                for signal in message.signals:
                    signal_item = QTreeWidgetItem(message_item)
                    signal_item.setText(1, signal.name)
                    signal_item.setData(0, Qt.UserRole, {"type": "signal", "data": signal, "msg_id": message.id})
                    checkbox = QCheckBox()
                    self.tree_widget.setItemWidget(signal_item, 0, checkbox)
                    self.signal_checkboxes[(message.id, signal.name)] = checkbox
                    self.all_signal_items.append(signal_item)
        # Ne pas expandAll, tout reste fermé par défaut
        # Sélectionner le premier signal pour affichage initial
        if self.tree_widget.topLevelItemCount() > 0:
            first_category = self.tree_widget.topLevelItem(0)
            if first_category.childCount() > 0:
                first_message = first_category.child(0)
                if first_message.childCount() > 0:
                    first_signal = first_message.child(0)
                    self.tree_widget.setCurrentItem(first_signal)
                    self.update_info_display(first_signal)
    
    def on_current_item_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """Gère le changement de sélection avec les touches fléchées"""
        if current is not None:
            self.update_info_display(current)
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Gère le clic sur un élément de l'arbre"""
        self.update_info_display(item)
    
    def update_info_display(self, item: QTreeWidgetItem):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data["type"] == "signal":
            signal = data["data"]
            msg_id = data["msg_id"]
            message = self.parser.messages.get(msg_id)
            if message:
                info_html = self._format_single_signal_info(signal, message)
                self.info_text.setHtml(info_html)
                self.statusBar().showMessage(f"Signal: {signal.name} (Message: {message.name} - ID: 0x{message.id:X})")
        elif data["type"] == "message":
            message = data["data"]
            info_html = self._format_complete_message_info(message)
            self.info_text.setHtml(info_html)
            self.statusBar().showMessage(f"Message: {message.name} - ID: 0x{message.id:X} - {len(message.signals)} signaux")
        elif data["type"] == "category":
            category = data["data"]
            messages = self.parser.categories[category]
            info_text = f"""
<h2>Catégorie: {category}</h2>
<p><b>Nombre de messages:</b> {len(messages)}</p>
<p><b>Messages dans cette catégorie:</b></p>
<ul>
"""
            for message in sorted(messages, key=lambda m: m.name):
                info_text += f"<li><b>{message.name}</b> (ID: 0x{message.id:X}) - {len(message.signals)} signaux</li>"
            info_text += "</ul>"
            self.info_text.setHtml(info_text)
            self.statusBar().showMessage(f"Catégorie: {category} - {len(messages)} messages")
    
    def _format_single_signal_info(self, signal: CANSignal, message: CANMessage) -> str:
        """Formate uniquement les informations du signal sélectionné"""
        html = f"""
<div style='font-family: Arial, sans-serif; padding: 10px;'>
    <h2 style='color: #2980b9;'>{signal.name}</h2>
    <table style='width: 100%; font-size: 13px;'>
        <tr><td><strong>Message:</strong></td><td>{message.name} (ID: 0x{message.id:X})</td></tr>
        <tr><td><strong>Position:</strong></td><td>bit {signal.start_bit}, longueur {signal.length} bits</td></tr>
        <tr><td><strong>Type:</strong></td><td>{signal.value_type}</td></tr>
        <tr><td><strong>Ordre:</strong></td><td>{signal.byte_order}</td></tr>
        <tr><td><strong>Facteur:</strong></td><td>{signal.factor}</td></tr>
        <tr><td><strong>Offset:</strong></td><td>{signal.offset}</td></tr>
"""
        if signal.minimum is not None or signal.maximum is not None:
            min_val = signal.minimum if signal.minimum is not None else 'N/A'
            max_val = signal.maximum if signal.maximum is not None else 'N/A'
            html += f"<tr><td><strong>Plage:</strong></td><td>[{min_val}, {max_val}]</td></tr>"
        if signal.unit:
            html += f"<tr><td><strong>Unité:</strong></td><td>{signal.unit}</td></tr>"
        if signal.receivers:
            receivers_text = ', '.join(signal.receivers)
            html += f"<tr><td><strong>Récepteurs:</strong></td><td>{receivers_text}</td></tr>"
        if signal.comment:
            html += f"<tr><td><strong>Commentaire:</strong></td><td style='font-style: italic; color: #7f8c8d;'>{signal.comment}</td></tr>"
        if signal.values:
            html += f"<tr><td><strong>Valeurs possibles:</strong></td><td>{', '.join([f'{k}: {v}' for k, v in signal.values.items()])}</td></tr>"
        html += "</table></div>"
        return html
    
    def update_info_display_with_highlight(self, item: QTreeWidgetItem):
        """Met à jour l'affichage avec surlignage des signaux correspondant à la recherche"""
        data = item.data(0, Qt.UserRole)
        
        if data["type"] == "message":
            message = data["data"]
            search_text = self.search_input.text().lower().strip()
            
            # Afficher les détails complets du message avec surlignage
            info_html = self._format_complete_message_info_with_highlight(message, search_text)
            self.info_text.setHtml(info_html)
            
            # Mettre à jour la barre de statut avec le nombre de résultats
            matching_signals = [s for s in message.signals if search_text in s.name.lower()]
            self.statusBar().showMessage(
                f"Message: {message.name} - {len(matching_signals)} signal(s) correspondant(s) trouvé(s)"
            )
    
    def _format_complete_message_info_with_highlight(self, message: CANMessage, search_text: str = "") -> str:
        """Formate les informations complètes d'un message avec surlignage des signaux correspondants"""
        html = f"""
<div style="font-family: Arial, sans-serif; padding: 10px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
        {message.name}
    </h2>
    
    <div style="background-color: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 5px;">
        <table style="width: 100%; font-size: 13px;">
            <tr><td style="width: 120px;"><strong>ID:</strong></td><td>0x{message.id:X} ({message.id})</td></tr>
            <tr><td><strong>Taille:</strong></td><td>{message.size} bytes</td></tr>
            <tr><td><strong>Transmetteur:</strong></td><td>{message.transmitter}</td></tr>
            <tr><td><strong>Catégorie:</strong></td><td>{message.category}</td></tr>
"""
        
        if message.comment:
            html += f"<tr><td><strong>Commentaire:</strong></td><td>{message.comment}</td></tr>"
        
        html += """
        </table>
    </div>
"""
        
        if message.signals:
            # Séparer les signaux correspondants et non correspondants
            matching_signals = []
            other_signals = []
            
            for signal in message.signals:
                if search_text and search_text in signal.name.lower():
                    matching_signals.append(signal)
                else:
                    other_signals.append(signal)
            
            # Afficher d'abord les signaux correspondants (surlignés)
            if matching_signals and search_text:
                html += f"""
    <h3 style="color: #e74c3c; margin-top: 20px;">
        🎯 Signaux correspondants ({len(matching_signals)})
    </h3>
"""
                for i, signal in enumerate(matching_signals, 1):
                    signal_html = self._format_signal_for_main_display_highlighted(signal, i, search_text)
                    html += signal_html
            
            # Puis afficher les autres signaux
            if other_signals:
                remaining_start = len(matching_signals) + 1
                html += f"""
    <h3 style="color: #27ae60; margin-top: 20px;">
        Autres signaux ({len(other_signals)})
    </h3>
"""
                for i, signal in enumerate(other_signals, remaining_start):
                    signal_html = self._format_signal_for_main_display(signal, i)
                    html += signal_html
        else:
            html += "<p><i>Aucun signal défini pour ce message.</i></p>"
        
        html += "</div>"
        return html
    
    def _format_signal_for_main_display_highlighted(self, signal: CANSignal, index: int, search_text: str) -> str:
        """Formate un signal avec surlignage pour l'affichage dans la zone principale"""
        # Surligner le texte de recherche dans le nom du signal
        highlighted_name = signal.name
        if search_text:
            # Remplacer le texte de recherche par une version surlignée (insensible à la casse)
            import re
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            highlighted_name = pattern.sub(f'<mark style="background-color: #ffeb3b; font-weight: bold;">{search_text}</mark>', signal.name)
        
        html = f"""
    <div style="background-color: #ffebee; margin: 8px 0; padding: 12px; border-left: 4px solid #e74c3c; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="color: #c62828; margin: 0 0 8px 0;">
            {index}. {highlighted_name}
        </h4>
        
        <table style="width: 100%; font-size: 12px;">
            <tr>
                <td style="width: 100px;"><strong>Position:</strong></td>
                <td>bit {signal.start_bit}, longueur {signal.length} bits</td>
            </tr>
            <tr>
                <td><strong>Type:</strong></td>
                <td>{signal.value_type}</td>
            </tr>
            <tr>
                <td><strong>Ordre:</strong></td>
                <td>{signal.byte_order}</td>
            </tr>
            <tr>
                <td><strong>Facteur:</strong></td>
                <td>{signal.factor}</td>
            </tr>
            <tr>
                <td><strong>Offset:</strong></td>
                <td>{signal.offset}</td>
            </tr>
"""
        
        if signal.minimum is not None or signal.maximum is not None:
            min_val = signal.minimum if signal.minimum is not None else 'N/A'
            max_val = signal.maximum if signal.maximum is not None else 'N/A'
            html += f"""
            <tr>
                <td><strong>Plage:</strong></td>
                <td>[{min_val}, {max_val}]</td>
            </tr>
"""
        
        if signal.unit:
            html += f"""
            <tr>
                <td><strong>Unité:</strong></td>
                <td>{signal.unit}</td>
            </tr>
"""
        
        if signal.receivers:
            receivers_text = ', '.join(signal.receivers)
            html += f"""
            <tr>
                <td><strong>Récepteurs:</strong></td>
                <td>{receivers_text}</td>
            </tr>
"""
        
        if signal.comment:
            html += f"""
            <tr>
                <td><strong>Commentaire:</strong></td>
                <td style="font-style: italic; color: #7f8c8d;">{signal.comment}</td>
            </tr>
"""
        
        if signal.values:
            html += f"""
            <tr>
                <td><strong>Valeurs possibles:</strong></td>
                <td>{', '.join([f'{k}: {v}' for k, v in signal.values.items()])}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
"""
        
        return html
    
    def on_search_text_changed(self, text: str):
        """Gère la recherche en temps réel dans les signaux des messages"""
        if not text.strip():
            self.current_search_results = []
            self.current_search_index = 0
            self.search_input.setFocus()  # Garder le focus sur le champ de recherche
            return
        search_text = text.lower().strip()
        self.current_search_results = []
        for item in self.all_signal_items:
            data = item.data(0, Qt.UserRole)
            if data and data["type"] == "signal":
                signal = data["data"]
                if search_text in signal.name.lower():
                    self.current_search_results.append(item)
        if self.current_search_results:
            self.current_search_index = 0
            self.select_search_result(self.current_search_index)
            self.statusBar().showMessage(f"Recherche de signaux: {len(self.current_search_results)} signal(s) contenant '{text}'")
        else:
            self.statusBar().showMessage(f"Aucun signal trouvé contenant '{text}'")
        self.search_input.setFocus()  # Garder le focus sur le champ de recherche

    def on_search_enter(self):
        """Gère l'appui sur Entrée pour naviguer dans les résultats de recherche"""
        if self.current_search_results:
            # Passer au résultat suivant (cyclique)
            self.current_search_index = (self.current_search_index + 1) % len(self.current_search_results)
            self.select_search_result(self.current_search_index)
            # Mettre à jour la barre de statut
            search_term = self.search_input.text()
            self.statusBar().showMessage(
                f"Signal '{search_term}': message {self.current_search_index + 1}/{len(self.current_search_results)}"
            )
        self.search_input.setFocus()  # Garder le focus sur le champ de recherche

    def select_search_result(self, index: int, keep_search_focus: bool = False):
        """Sélectionne un résultat de recherche spécifique"""
        if 0 <= index < len(self.current_search_results):
            item = self.current_search_results[index]
            parent = item.parent()
            if parent:
                parent.setExpanded(True)
            self.tree_widget.setCurrentItem(item)
            self.tree_widget.scrollToItem(item, QTreeWidget.PositionAtCenter)
            self.update_info_display(item)
            if keep_search_focus:
                self.search_input.setFocus()
    
    def _format_complete_message_info(self, message: CANMessage) -> str:
        """Formate les informations complètes d'un message pour l'affichage dans la zone principale"""
        html = f"""
<div style="font-family: Arial, sans-serif; padding: 10px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
        {message.name}
    </h2>
    
    <div style="background-color: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 5px;">
        <table style="width: 100%; font-size: 13px;">
            <tr><td style="width: 120px;"><strong>ID:</strong></td><td>0x{message.id:X} ({message.id})</td></tr>
            <tr><td><strong>Taille:</strong></td><td>{message.size} bytes</td></tr>
            <tr><td><strong>Transmetteur:</strong></td><td>{message.transmitter}</td></tr>
            <tr><td><strong>Catégorie:</strong></td><td>{message.category}</td></tr>
"""
        
        if message.comment:
            html += f"<tr><td><strong>Commentaire:</strong></td><td>{message.comment}</td></tr>"
        
        html += """
        </table>
    </div>
"""
        
        if message.signals:
            html += f"""
    <h3 style="color: #27ae60; margin-top: 20px;">
        Signaux ({len(message.signals)})
    </h3>
"""
            
            for i, signal in enumerate(message.signals, 1):
                signal_html = self._format_signal_for_main_display(signal, i)
                html += signal_html
        else:
            html += "<p><i>Aucun signal défini pour ce message.</i></p>"
        
        html += "</div>"
        return html
    
    def _format_signal_for_main_display(self, signal: CANSignal, index: int) -> str:
        """Formate un signal pour l'affichage dans la zone principale"""
        html = f"""
    <div style="background-color: #f8f9fa; margin: 8px 0; padding: 12px; border-left: 4px solid #3498db; border-radius: 3px;">
        <h4 style="color: #2980b9; margin: 0 0 8px 0;">
            {index}. {signal.name}
        </h4>
        
        <table style="width: 100%; font-size: 12px;">
            <tr>
                <td style="width: 100px;"><strong>Position:</strong></td>
                <td>bit {signal.start_bit}, longueur {signal.length} bits</td>
            </tr>
            <tr>
                <td><strong>Type:</strong></td>
                <td>{signal.value_type}</td>
            </tr>
            <tr>
                <td><strong>Ordre:</strong></td>
                <td>{signal.byte_order}</td>
            </tr>
            <tr>
                <td><strong>Facteur:</strong></td>
                <td>{signal.factor}</td>
            </tr>
            <tr>
                <td><strong>Offset:</strong></td>
                <td>{signal.offset}</td>
            </tr>
"""
        
        if signal.minimum is not None or signal.maximum is not None:
            min_val = signal.minimum if signal.minimum is not None else 'N/A'
            max_val = signal.maximum if signal.maximum is not None else 'N/A'
            html += f"""
            <tr>
                <td><strong>Plage:</strong></td>
                <td>[{min_val}, {max_val}]</td>
            </tr>
"""
        
        if signal.unit:
            html += f"""
            <tr>
                <td><strong>Unité:</strong></td>
                <td>{signal.unit}</td>
            </tr>
"""
        
        if signal.receivers:
            receivers_text = ', '.join(signal.receivers)
            html += f"""
            <tr>
                <td><strong>Récepteurs:</strong></td>
                <td>{receivers_text}</td>
            </tr>
"""
        
        if signal.comment:
            html += f"""
            <tr>
                <td><strong>Commentaire:</strong></td>
                <td style="font-style: italic; color: #7f8c8d;">{signal.comment}</td>
            </tr>
"""
        
        if signal.values:
            html += f"""
            <tr>
                <td><strong>Valeurs possibles:</strong></td>
                <td>{', '.join([f'{k}: {v}' for k, v in signal.values.items()])}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
"""
        
        return html
    
    def export_selected_to_json(self):
        import json
        selected = []
        for (msg_id, signal_name), checkbox in self.signal_checkboxes.items():
            if checkbox.isChecked() and msg_id in self.parser.messages:
                msg = self.parser.messages[msg_id]
                sig = next((s for s in msg.signals if s.name == signal_name), None)
                if sig:
                    sig_dict = {
                        "message_id": msg.id,
                        "message_name": msg.name,
                        "message_category": msg.category,
                        "signal_name": sig.name,
                        "start_bit": sig.start_bit,
                        "length": sig.length,
                        "byte_order": sig.byte_order,
                        "value_type": sig.value_type,
                        "factor": sig.factor,
                        "offset": sig.offset,
                        "minimum": sig.minimum,
                        "maximum": sig.maximum,
                        "unit": sig.unit,
                        "receivers": sig.receivers,
                        "comment": sig.comment,
                        "values": sig.values
                    }
                    selected.append(sig_dict)
        json_str = json.dumps(selected, indent=2, ensure_ascii=False)
        self.info_text.setPlainText(json_str)


def main():
    """Point d'entrée principal"""
    app = QApplication(sys.argv)
    app.setApplicationName("Analyseur DBC Tesla Model 3")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()