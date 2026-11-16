FROM python:3.9-slim

# System libraries required by the Qt backend of matplotlib
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxext6 \
    libsm6 \
    libxrender1 \
    libqt5widgets5 \
    libqt5gui5 \
    libqt5core5a \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (same pinned list as the native installation)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Working directory: mount the host one here to load/save the session files
WORKDIR /home

COPY plot.py /app/plot.py

ENTRYPOINT ["python", "/app/plot.py"]
CMD []
