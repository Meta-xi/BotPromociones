import requests
import asyncio

class processMessage :
    def __init__(self) -> None:
        pass
    async def GetMessageToApi(self ,api_url):
        def make_request():
            response = requests.get(api_url)
            try:
                return response.status_code , response.json()
            except:
                return response.status_code , {"Message" : f"Error a la hora de obtener los mensajes"}
        status_code , response_data = await asyncio.to_thread(make_request)
        return status_code , response_data
    @staticmethod
    def Split_Array_Dates(dates , size = 20):
        return [dates[i:i+size] for i in range(0 , len(dates) , size)]