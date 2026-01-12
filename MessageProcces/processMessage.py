import requests
import asyncio

class processMessage :
    def __init__(self) -> None:
        pass
    async def GetMessageToApi(self ,api_url):
        def make_request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.get(api_url)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , {"Message" : f"Error a la hora de obtener los mensajes"}
        status_code , response_data = await asyncio.to_thread(make_request)
        return status_code , response_data
    @staticmethod
    def Split_Array_Dates(dates , size = 20):
        return [dates[i:i+size] for i in range(0 , len(dates) , size)]
    async def GetMessagesToUpdate(self ,api_url ,headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.get(api_url , headers=headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , {"Message" : f"Error a la hora de obtener los mensajes"}
        status_code , response_data = await asyncio.to_thread(Make_Request)
        return status_code , response_data
    async def update_configs(self , api_url , configs , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.patch(api_url , json = configs , headers=headers)
            try:
                return response.status_code , response.json()
            except Exception as e:
                print("⚠️ Error al parsear JSON de la respuesta:")
                print(response.text)
                print("Excepción capturada:", e)
                return response.status_code , {"Message" : f"Error a la hora de actualizar los mensajes"}
        status_code , response_data = await asyncio.to_thread(Make_Request)
        return status_code , response_data
    async def delete_one_config(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.delete(api_url , headers = headers)
            try: 
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        status_code , response_data = await asyncio.to_thread(Make_Request)
        return status_code , response_data
    async def Delete_all_config(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.delete(api_url , headers = headers )
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        status_code , response_data = await asyncio.to_thread(Make_Request)
        return status_code , response_data
    async def GetConfigsEnable(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.get(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , {"Message" : f"Error a la hora de obtener los mensajes"}
        code , data = await asyncio.to_thread(Make_Request)
        return code , data
    async def pause_one_config(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.patch(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        code , data = await asyncio.to_thread(Make_Request)
        return code , data
    async def pause_all_configs(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.patch(api_url , headers = headers )
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        code , response = await asyncio.to_thread(Make_Request)
        return code ,response
    async def getConfigsDisabled(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.get(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        code , response = await asyncio.to_thread(Make_Request)
        return code , response
    async def play_one_config(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.patch(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        code , response = await asyncio.to_thread(Make_Request)
        return code , response 
    async def play_all_configs(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False  # Esto ignora variables de entorno relacionadas con proxy
            response = session.patch(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json() 
        code , response = await asyncio.to_thread(Make_Request)
        return code , response      