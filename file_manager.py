import os
from datetime import datetime
from unicodedata import name
import uuid

class FileManager:
    def __init__(self ,base_path= "Files"):
        self.base_path = base_path
        self.Directory_Create()
        
    def Directory_Create(self):
        os.makedirs(self.base_path , exist_ok=True)
        for type in ['image' , 'video' , 'document']:
            os.makedirs(os.path.join(self.base_path , type) ,exist_ok=True)
    def Unique_route_generate(self, file_type, extension):
        date = datetime.now().strftime("%Y_%m_%d")
        unique_id = str(uuid.uuid4())[:8]
        name = f"{file_type}_{date}_{unique_id}.{extension}"
        return os.path.join(self.base_path ,file_type , name)
    def Save_File(self, content ,file_type , extension):
        route = self.Unique_route_generate(file_type ,extension)
        with open(route , 'wb') as f:
            f.write(content)
        return route
    def get_files(self , route):
        if os.path.exists(route):
            with open(route , 'rb') as f:
                return f.read()
        return None