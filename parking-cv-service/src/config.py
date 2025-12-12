"""
Configuration module for parking CV service.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the parking CV service."""
    
    # Backend API settings
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "")
    
    # Model paths
    VEHICLE_MODEL_PATH = os.getenv("VEHICLE_MODEL_PATH", "models/vehicle_yolov8n.pt")
    PLATE_MODEL_PATH = os.getenv("PLATE_MODEL_PATH", "models/plate_yolov8n.pt")
    
    # Detection settings
    VEHICLE_CONFIDENCE_THRESHOLD = float(os.getenv("VEHICLE_CONFIDENCE_THRESHOLD", "0.5"))
    PLATE_CONFIDENCE_THRESHOLD = float(os.getenv("PLATE_CONFIDENCE_THRESHOLD", "0.6"))
    
    # OCR settings
    OCR_LANGUAGES = ["en"]
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7"))
    
    # Camera settings
    ENTRY_CAMERA_URL = os.getenv("ENTRY_CAMERA_URL", "0")
    INDOOR_CAMERA_URL = os.getenv("INDOOR_CAMERA_URL", "1")
    
    # Processing settings
    FRAME_SKIP = int(os.getenv("FRAME_SKIP", "5"))
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        if not cls.BACKEND_URL:
            raise ValueError("BACKEND_URL is required")
        return True
