FROM python:3.9-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /home

# Copiar los archivos de la aplicación
COPY plot.py /app/plot.py

# Instalar las dependencias de Python
RUN pip install --no-cache-dir matplotlib PyQt5 numpy pandas

ENTRYPOINT ["python", "/app/plot.py"]
CMD []

