"""Vehicle Detection Module using YOLOv8

Handles real-time vehicle detection for entry/exit gates and indoor monitoring.
Detects cars, bikes, and classifies vehicle types for automatic slot assignment.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Dict, Optional
import logging
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Detection:
    """Vehicle detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    center_point: Tuple[int, int]
    timestamp: datetime
    
class VehicleDetector:
    """YOLOv8-based vehicle detector for mall parking system"""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize vehicle detector
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        # Vehicle classes we're interested in
        self.vehicle_classes = {
            'car': ['car', 'truck', 'van', 'suv'],
            'bike': ['motorcycle', 'bicycle', 'scooter']
        }
        
        # Initialize model
        self._load_model()
        
    def _load_model(self):
        """Load YOLOv8 model"""
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"YOLOv8 model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect vehicles in a frame
        
        Args:
            frame: Input image frame
            
        Returns:
            List of vehicle detections
        """
        if self.model is None:
            return []
            
        try:
            # Run YOLO inference
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract detection data
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Get class name
                        class_name = self.model.names[class_id]
                        
                        # Check if it's a vehicle we care about
                        vehicle_type = self._classify_vehicle_type(class_name)
                        if vehicle_type:
                            # Calculate bounding box and center
                            bbox = (int(x1), int(y1), int(x2-x1), int(y2-y1))
                            center = (int((x1+x2)/2), int((y1+y2)/2))
                            
                            detection = Detection(
                                class_name=vehicle_type,
                                confidence=confidence,
                                bbox=bbox,
                                center_point=center,
                                timestamp=datetime.now()
                            )
                            detections.append(detection)
                            
            return detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def _classify_vehicle_type(self, yolo_class: str) -> Optional[str]:
        """
        Map YOLO class to our vehicle types (CAR/BIKE)
        
        Args:
            yolo_class: YOLO detected class name
            
        Returns:
            'CAR' or 'BIKE' or None if not a vehicle
        """
        yolo_class = yolo_class.lower()
        
        for vehicle_type, class_names in self.vehicle_classes.items():
            if any(cls in yolo_class for cls in class_names):
                return 'CAR' if vehicle_type == 'car' else 'BIKE'
                
        return None
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detection bounding boxes on frame
        
        Args:
            frame: Input frame
            detections: List of detections to draw
            
        Returns:
            Frame with drawn detections
        """
        result_frame = frame.copy()
        
        for detection in detections:
            x, y, w, h = detection.bbox
            confidence = detection.confidence
            class_name = detection.class_name
            
            # Choose color based on vehicle type
            color = (0, 255, 0) if class_name == 'CAR' else (255, 0, 0)  # Green for car, blue for bike
            
            # Draw bounding box
            cv2.rectangle(result_frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background for label
            cv2.rectangle(result_frame, (x, y - label_size[1] - 10), 
                         (x + label_size[0], y), color, -1)
            
            # Label text
            cv2.putText(result_frame, label, (x, y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_frame
    
    def is_vehicle_in_zone(self, detection: Detection, zone_coords: Tuple[int, int, int, int]) -> bool:
        """
        Check if detected vehicle is within a defined zone (ROI)
        
        Args:
            detection: Vehicle detection
            zone_coords: Zone coordinates (x, y, width, height)
            
        Returns:
            True if vehicle center is within zone
        """
        zone_x, zone_y, zone_w, zone_h = zone_coords
        vehicle_center_x, vehicle_center_y = detection.center_point
        
        return (zone_x <= vehicle_center_x <= zone_x + zone_w and 
                zone_y <= vehicle_center_y <= zone_y + zone_h)
    
    def get_model_info(self) -> Dict[str, str]:
        """Get model information"""
        return {
            "model_path": self.model_path,
            "confidence_threshold": str(self.confidence_threshold),
            "supported_classes": str(list(self.vehicle_classes.keys())),
            "model_loaded": str(self.model is not None)
        }