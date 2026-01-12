FROM python:3.9-slim

WORKDIR /app

# Copiar solo requirements primero (mejor cache)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

CMD ["python", "bot2.py"]
