# Usar una imagen base oficial de Python, usamos 'BULLSEYE' (Debian 11)
FROM python:3.10-bullseye

# Configuración básica
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar TODO el stack de GStreamer y Audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    ca-certificates \
    libasound2 \
    libasound2-plugins \
    wget \
    # Librerías GStreamer (El motor de audio)
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    gstreamer1.0-alsa \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando de arranque
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]