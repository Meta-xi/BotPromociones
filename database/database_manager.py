import sqlite3
import os

class DataBasemanager:
    def __init__(self , db_name="database/jwt.db"):
        self.db_name = db_name
        self.initializeDB()
    def initializeDB(self):
        print(f"Verificando existencia de la base de datos: {self.db_name}")
        if not os.path.exists(self.db_name):
            print("La base de datos no existe. Creando...")
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                           CREATE TABLE IF NOT EXISTS userTokens(
                               idUserTelegram INTEGER PRIMARY KEY,
                               JWT TEXT
                           )
                           """) 
            conn.commit()
        else:
            print("La base de datos ya existe.")
    def save_token(self , idUserTelegram , jwt):
        with sqlite3.connect(self.db_name) as connect:
            cursor = connect.cursor()
            cursor.execute("""
                           INSERT INTO userTokens(idUserTelegram , JWT) 
                           VALUES (?,?)
                           ON CONFLICT(idUserTelegram) DO UPDATE SET JWT = excluded.JWT
                           """,(idUserTelegram , jwt))
            connect.commit()
    def get_token(self , idUserTelegram):
        with sqlite3.connect(self.db_name) as connect:
            cursor = connect.cursor()
            cursor.execute("""
                           SELECT JWT FROM userTokens WHERE idUserTelegram = ? 
                           """,(idUserTelegram,))
            result = cursor.fetchone()
            return result[0] if result else None
    def delete_token(self , idUserTelegram):
        with sqlite3.connect(self.db_name) as connect:
            cursor = connect.cursor()
            cursor.execute("""
                           DELETE FROM userTokens WHERE idUserTelegram = ?
                           """,(idUserTelegram,))
            connect.commit()

        
        