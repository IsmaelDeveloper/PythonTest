import sqlite3

class LocalDbParameterStorage:
    def __init__(self) : 
        self.connexion = sqlite3.connect('data.db')

        self.cursor = self.connexion.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = self.cursor.fetchall()
        for table in tables:
            print(table[0])

        self.connexion.close()
