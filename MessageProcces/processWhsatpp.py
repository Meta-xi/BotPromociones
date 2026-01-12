import asyncio
import requests
import json



class processWhatsapp:
    def __init__(self) -> None:
        pass
    async def Conect_To_Whatsapp(self , api_url , data , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False
            response = session.post(api_url , json = data , headers = headers)
            print(response.text)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        status_code , response = await asyncio.to_thread(Make_Request)
        return status_code , response
    async def Get_Groups(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False
            response = session.get(api_url , headers = headers)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , response.json()
        status_code , response = await asyncio.to_thread(Make_Request)
        return status_code , response
    async def GetInstanceName(self , api_url , headers):
        def Make_Request():
            session = requests.Session()
            session.trust_env = False
            response = session.get(api_url , headers = headers)
            try:
              return response.status_code , response.text.strip()  
            except:
                return response.status_code , response.json()
        status_code , response = await asyncio.to_thread(Make_Request)
        return status_code , response
    async def CreateConfigToWhatsapp(self, api_url, data , headers):
        def Make_Request():
            try:
                session = requests.Session()
                session.trust_env = False  # FIX: era "trus_env", debe ser "trust_env"
            
                # Extraer la imagen por separado
                imagen_bytes = data.get('imagen')
            
                # Preparar datos del formulario (sin la imagen)
                form_data = {
                    "chat_id": str(data.get("chat_id", "")),
                    "ids_destino": data.get("ids_destino", []),  # Convertir lista a JSON string
                    "caption": data.get("caption", ""),
                    "intervalo": str(data.get("intervalo", 0))
                }
            
                # Preparar archivo si existe
                files = None
                if imagen_bytes and isinstance(imagen_bytes, bytes) and len(imagen_bytes) > 0:
                    files = {'imagen': ('imagen.jpg', imagen_bytes, 'image/jpeg')}
            
                # Enviar como multipart/form-data
                # Usar data= para campos normales y files= para archivos
                if files:
                    response = session.post(api_url, data=form_data, files=files, timeout=30 , headers = headers)
                else:
                    response = session.post(api_url, data=form_data, timeout=30 , headers = headers)
            
                try:
                    return response.status_code, response.json()
                except:
                    return response.status_code, response.text  # Si no es JSON, devolver texto
            
            except Exception as e:
                print(f"Error en CreateConfigToWhatsapp: {e}")
                return 500, None
    
        status_code, response = await asyncio.to_thread(Make_Request)
        return status_code, response