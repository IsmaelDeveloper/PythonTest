import json
import os


class LocalParameterStorage:
    def __init__(self, file_path='parameters.json'):
        self.file_path = file_path
        self.ensure_parameters_exist()

    def ensure_parameters_exist(self):
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as file:
                json.dump({'isDate': True, 'isName': True,
                          'isTemperature': True}, file)

    def get_parameters(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def set_parameter(self, key, value):
        parameters = self.get_parameters()
        parameters[key] = value
        with open(self.file_path, 'w') as file:
            json.dump(parameters, file)

    def save_parameters(self, params):
        with open(self.file_path, 'w') as file:
            json.dump(params, file)

# Utilisation de la classe
# storage = LocalParameterStorage()

# # Obtenir les paramètres
# params = storage.get_parameters()
# print(params)

# # Modifier un paramètre
# storage.set_parameter('isDate', False)
