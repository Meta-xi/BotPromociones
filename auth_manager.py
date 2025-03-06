import requests
import asyncio
from telethon.sessions import StringSession
from telethon import TelegramClient
import database.database_manager as database_manager

class AuthManager:
    def __init__(self, api_id, api_hash, api_url="http://localhost:3000/user/" , db_name="jwt.db"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.api_url = api_url
        self.db = database_manager.DataBasemanager(db_name)

    async def sign_in(self, phone_number, client):
        try:
            # Obtener la string session
            string_session = StringSession.save(client.session)
            
            # Obtener el ID del usuario (correctamente awaited)
            me = await client.get_me()
            user_id = me.id
            
            # Datos para enviar a la API
            data = {
                "sesionToken": string_session,
                "idUserTelegram": user_id,
            }

            # Realizar la petición a la API de forma asíncrona usando asyncio.to_thread
            def make_request():
                response = requests.post(f"{self.api_url}", json=data)
                try:
                    return response.status_code, response.json()
                except:
                    return response.status_code, {"message": f"Error en la autenticación: Status {response.status_code}"}

            status_code, response_data = await asyncio.to_thread(make_request)
            if status_code == 200:
                token = response_data.get('token')
                if token:
                    self.db.save_token(user_id , token)
                    return True, response_data.get('message', 'Autenticación exitosa')
            else:
                return False, response_data.get('message', 'Error en la autenticación')

        except Exception as e:
            return False, f"Error durante la autenticación: {e}"
    async def logout(self, client):
        try:
            # Obtener la string session
            string_session = StringSession.save(client.session)
            
            # Obtener el ID del usuario
            me = await client.get_me()
            user_id = me.id
            token = self.db.get_token(user_id)
            if not token:
                return False, "El usuario no esta conectado"
            
            # Datos para enviar a la API
            data = {
                'idUserTelegram': user_id,
                'sesionToken': ""
            }
            headers = {
                'Authorization' : f"Bearer {token}",
                'Content-Type' : 'application/json'
            }

            # Realizar la petición a la API de forma asíncrona
            def make_request():
                response = requests.put(f"{self.api_url}", json=data , headers=headers)
                try:
                    return response.status_code, response.json()
                except:
                    return response.status_code, {"message": f"Error en la desconexión: Status {response.status_code}"}

            status_code, response_data = await asyncio.to_thread(make_request)
            
            if status_code == 200:
                self.db.delete_token(user_id)
                return True, response_data.get('message', 'Desconectado exitosamente')
            else:
                return False, response_data.get('message', 'Error al desconectarse')

        except Exception as e:
            return False, f"Error durante la desconexión: {e}"
    @staticmethod
    async def create_client(phone_number, api_id, api_hash):
        """
        Crear un nuevo cliente de Telegram
        Args:
            phone_number: Número de teléfono del usuario
            api_id: ID de la API de Telegram
            api_hash: Hash de la API de Telegram
        Returns:
            TelegramClient: Cliente de Telegram configurado
        """
        # Usamos el número de teléfono como identificador de sesión
        client = TelegramClient(phone_number, api_id, api_hash)
        return client
