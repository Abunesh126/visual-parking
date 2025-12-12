"""Computer Vision module for Mall Parking System

This module provides:
- Vehicle detection using YOLOv8
- License plate recognition (ANPR)
- Real-time camera stream processing
- Slot occupancy detection
"""

from .detector import VehicleDetector
from .anpr import LicensePlateRecognizer  
from .camera_manager import CameraManager
from .slot_detector import SlotOccupancyDetector

__all__ = [
    "VehicleDetector",
    "LicensePlateRecognizer", 
    "CameraManager",
    "SlotOccupancyDetector"
]