import requests
from telethon.client import dialogs
import database.database_manager as database_manager
from telethon import TelegramClient
from telethon.sessions import StringSession

class groupsandchannel:
    def __init__(self ,api_id: int , api_hash : str ,dbname = "jwt.db"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.db = database_manager.DataBasemanager(dbname)
    
    def getStringSession(self , chat_id: int)-> str :
        try:
            token = self.db.get_token(chat_id);
            if not token:
                return None
            else:
                headers = {
                'Authorization' : f"Bearer {token}",
                'Content-Type' : 'application/json'
                }
                response = requests.get(f"http://localhost:3000/user/StringSession/{chat_id}" , headers=headers)
                if response.status_code == 200:
                    return response.json().get('stringSession')
                else:
                    return None
        except Exception as e:
            print(f"Error al obtener la StringSession para el chat_id: {chat_id}: {e}")
            return None

        
        
        