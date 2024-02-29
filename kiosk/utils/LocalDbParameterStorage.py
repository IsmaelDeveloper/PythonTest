import sqlite3

class LocalDbParameterStorage:
    def __init__(self, db_path='data.db'):
        self.db_path = db_path
        self.connexion = sqlite3.connect(self.db_path)
        self.cursor = self.connexion.cursor()
        self.ensure_table_exists()

    def ensure_table_exists(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS parameters (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
        self.cursor.execute(create_table_query)
        self.connexion.commit()

    def get_parameters(self):
        query = "SELECT key, value FROM parameters"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return {key: value for key, value in rows}

    def set_parameter(self, key, value):
        query = "INSERT INTO parameters (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
        self.cursor.execute(query, (key, value))
        self.connexion.commit()

    def reset_parameters(self):
        default_params = {
            'isDate': 'True', 'isName': 'True',
            'isTemperature': 'True', 'highTemperatureAlarm': 'True', 'isMaskAlarm': 'True',
            'temperature': '37.0', 'movement': '15', 'movementVertical': '20', 'width': '800',
            'height': '400', 'offsetTemperature': '0.0', "WDR": 'False', 'screenOption': 'True'
        }
        self.cursor.execute("DELETE FROM parameters")
        for key, value in default_params.items():
            self.set_parameter(key, value)

    def close_connection(self):
        self.connexion.close()
