"""
Models package for vehicle and plate detection.
"""
from .vehicle_detector import VehicleDetector
from .plate_detector import PlateDetector
from .plate_ocr import PlateOCR

__all__ = ["VehicleDetector", "PlateDetector", "PlateOCR"]
