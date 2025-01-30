import sqlite3

class DataBasemanager:
    def __init__(self , db_name="jwt.db"):
        self.db_name = db_name
        self.initializeDB()
    def initializeDB(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS userTokens(
                               idUserTelegram INTEGER PRIMARY KEY,
                               JWT TEXT
                           )
                           """) 
            conn.commit()
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

        
        