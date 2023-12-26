import json
import os


class LocalParameterStorage:
    def __init__(self, file_path='parameters.json'):
        self.file_path = file_path
        self.ensure_parameters_exist()

    def ensure_parameters_exist(self):
        if not os.path.exists(self.file_path):
            self.reset_parameters()

    def get_parameters(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def set_parameter(self, key, value):
        parameters = self.get_parameters()
        parameters[key] = value
        self.save_parameters(parameters)

    def save_parameters(self, params):
        with open(self.file_path, 'w') as file:
            json.dump(params, file)

    def reset_parameters(self):
        default_params = {
            'isDate': True, 'isName': True,
            'isTemperature': True, 'highTemperatureAlarm': True, 'isMaskAlarm': True,
            'temperature': 37.0, 'movement': 15, 'movementVertical': 20, 'width': 800,
            'height': 400, 'offsetTemperature': 0.0, "WDR": False, 'screenOption': True
        }
        self.save_parameters(default_params)

# Utilisation de la classe
# storage = LocalParameterStorage()

# Réinitialiser et sauvegarder les paramètres par défaut
# storage.reset_parameters()
