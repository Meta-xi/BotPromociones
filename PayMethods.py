import requests
from urllib3 import request, response

class PayMethods:
    def __init__(self , criptobot_Token: str):
        self.cryptobotToken = criptobot_Token
        self.api_url = 'https://testnet-pay.crypt.bot/'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.cryptbot_token}'
        }
        self.backend_url = ''
    async def create_invoice(self , currency: str , amount: str , description: str):
        url = self.api_url + "api/createInvoice"
        data = {
            'asset': currency,
            'amount': amount,
            'description': description
        }
        response = requests.post(url , json= data  , headers= self.headers)
        return response.json()
    async def check_invoice(self, invoice_id: str):
        url = self.api_url + "api/getInvoice"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.cryptobot_token}'
        }
        data = {'invoice_id': invoice_id}
        response = requests.post(url , json=data , headers= headers)
        return response.json()
    async def send_new_Transaction(self ,id_invoice , user_id: int , price: float ):
        ''' headers = {
            'Content-Type' : 'application/json'
        } '''
        data = {
            id_invoice : id_invoice,
            user_id : user_id,
            price : price,
        }
        response = requests.post(self.backend_url , json= data , headers = headers)
        return response.status_code , response.json()
    async def get_transactions(self ,):
        response = requests.get(self.backend_url )
        return response.json()
    async def send_modify_transactions(self, payments):
        response = requests.patch(self.backend_url , json = payments)
        return response.status_code , response.json()