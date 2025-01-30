# Usamos una imagen base de Python
FROM python:3.9-slim

# Establecemos el directorio de trabajo en el contenedor
WORKDIR /app

# Copiamos el código de tu bot al contenedor
COPY . /app

# Instalamos las dependencias necesarias desde el archivo requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto si es necesario (para bots no es obligatorio, pero algunos requieren un webhook)
EXPOSE 5000

# Comando para ejecutar el bot
CMD ["python", "bot2.py"]

