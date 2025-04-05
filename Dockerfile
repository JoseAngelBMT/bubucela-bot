FROM python:3.12-slim

WORKDIR /


RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libopenblas-dev \
    liblapack-dev \
    ffmpeg \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY .env .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando por defecto
CMD ["python", "bot/bot.py"]