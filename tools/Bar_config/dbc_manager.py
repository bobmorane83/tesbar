import cantools
import json
import os

class DBCManager:
    def __init__(self, dbc_file='tesla_can.dbc'):
        self.dbc_file = dbc_file
        self.db = None
        self.messages = {}
        self.signals = {}
        self.load_dbc()

    def load_dbc(self):
        if os.path.exists(self.dbc_file):
            self.db = cantools.database.load_file(self.dbc_file)
            self.extract_data()
        else:
            print(f"DBC file {self.dbc_file} not found.")

    def extract_data(self):
        for message in self.db.messages:
            self.messages[message.name] = {
                'id': message.frame_id,
                'name': message.name,
                'length': message.length,
                'signals': {}
            }
            for signal in message.signals:
                self.signals[f"{message.name}.{signal.name}"] = {
                    'message_id': message.frame_id,
                    'message_name': message.name,
                    'signal_name': signal.name,
                    'start': signal.start,
                    'length': signal.length,
                    'byte_order': signal.byte_order,
                    'is_signed': signal.is_signed,
                    'scale': signal.scale,
                    'offset': signal.offset,
                    'minimum': signal.minimum,
                    'maximum': signal.maximum,
                    'unit': signal.unit,
                    'choices': signal.choices,
                    'comment': signal.comment
                }
                self.messages[message.name]['signals'][signal.name] = self.signals[f"{message.name}.{signal.name}"]

    def get_message_names(self):
        return list(self.messages.keys())

    def get_signal_names(self):
        return list(self.signals.keys())

    def get_message_by_name(self, name):
        return self.messages.get(name)

    def get_signal_by_name(self, name):
        return self.signals.get(name)

    def get_signals_for_message(self, message_name):
        if message_name in self.messages:
            return list(self.messages[message_name]['signals'].keys())
        return []

    def get_signal_values(self, signal_name):
        """Retourne les valeurs possibles pour un signal"""
        signal = self.get_signal_by_name(signal_name)
        if signal and signal.get('choices'):
            return signal['choices']
        return {}

    def get_signal_value_names(self, signal_name):
        """Retourne la liste des noms de valeurs pour un signal"""
        values = self.get_signal_values(signal_name)
        names = []
        for value, name in sorted(values.items()):
            # Convert NamedSignalValue to string
            if hasattr(name, 'name'):
                names.append(name.name)
            else:
                names.append(str(name))
        return names

if __name__ == "__main__":
    manager = DBCManager()
    print("Messages:", len(manager.get_message_names()))
    print("Signals:", len(manager.get_signal_names()))
    
    # Test avec un signal qui devrait avoir des valeurs
    test_signals = [s for s in manager.get_signal_names() if 'DI_state' in s]
    if test_signals:
        signal_name = test_signals[0]
        print(f"Test signal: {signal_name}")
        values = manager.get_signal_values(signal_name)
        print(f"Values: {values}")
        value_names = manager.get_signal_value_names(signal_name)
        print(f"Value names: {value_names}")
