# Usar una imagen base oficial de Python ligera
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc y buffer de salida
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para Azure Speech y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    ca-certificates \
    libasound2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto 8000
EXPOSE 8000

# Comando para iniciar la aplicación
# Usamos la ruta completa src.api.main:app
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]