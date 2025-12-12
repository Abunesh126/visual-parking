"""
Vehicle detection module using YOLOv8.
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class VehicleDetector:
    """Detects vehicles in images using YOLOv8."""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        Initialize the vehicle detector.
        
        Args:
            model_path: Path to the YOLOv8 model weights
            confidence_threshold: Minimum confidence score for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self._load_model()
        
        # Vehicle class IDs in COCO dataset
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
    
    def _load_model(self):
        """Load the YOLOv8 model."""
        try:
            logger.info(f"Loading vehicle detection model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("Vehicle detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load vehicle detection model: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List[dict]:
        """
        Detect vehicles in an image.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detections, each containing bbox, confidence, and class_id
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    
                    # Filter only vehicle classes
                    if class_id in self.vehicle_classes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        
                        detections.append({
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': self.model.names[class_id]
                        })
            
            logger.debug(f"Detected {len(detections)} vehicles")
            return detections
            
        except Exception as e:
            logger.error(f"Error during vehicle detection: {e}")
            return []
    
    def get_largest_vehicle(self, detections: List[dict]) -> Optional[dict]:
        """
        Get the largest vehicle detection from a list of detections.
        
        Args:
            detections: List of vehicle detections
            
        Returns:
            Largest detection or None if no detections
        """
        if not detections:
            return None
        
        largest = max(detections, key=lambda d: self._bbox_area(d['bbox']))
        return largest
    
    @staticmethod
    def _bbox_area(bbox: List[int]) -> int:
        """Calculate bounding box area."""
        x1, y1, x2, y2 = bbox
        return (x2 - x1) * (y2 - y1)
    
    def draw_detections(self, image: np.ndarray, detections: List[dict]) -> np.ndarray:
        """
        Draw bounding boxes on image.
        
        Args:
            image: Input image
            detections: List of detections
            
        Returns:
            Image with drawn bounding boxes
        """
        img_copy = image.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            confidence = det['confidence']
            class_name = det['class_name']
            
            # Draw bounding box
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(img_copy, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return img_copy
