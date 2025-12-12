FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY parking_spots.json .
COPY .env .

# Create models directory
RUN mkdir -p models

# Download default YOLOv8 model (can be overridden with volume mount)
RUN wget -q https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/vehicle_yolov8n.pt

# Set Python path
ENV PYTHONPATH=/app/src

# Default command (can be overridden in docker-compose)
CMD ["python", "src/main_entry.py"]
