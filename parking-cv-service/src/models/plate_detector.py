"""
License plate detection module using YOLOv8.
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class PlateDetector:
    """Detects license plates in images using YOLOv8."""
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.6):
        """
        Initialize the plate detector.
        
        Args:
            model_path: Path to the YOLOv8 model weights
            confidence_threshold: Minimum confidence score for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the YOLOv8 model."""
        try:
            logger.info(f"Loading plate detection model from {self.model_path}")
            self.model = YOLO(self.model_path)
            logger.info("Plate detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load plate detection model: {e}")
            raise
    
    def detect(self, image: np.ndarray) -> List[dict]:
        """
        Detect license plates in an image.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detections, each containing bbox and confidence
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        try:
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': confidence
                    })
            
            logger.debug(f"Detected {len(detections)} license plates")
            return detections
            
        except Exception as e:
            logger.error(f"Error during plate detection: {e}")
            return []
    
    def detect_in_roi(self, image: np.ndarray, roi_bbox: List[int]) -> List[dict]:
        """
        Detect license plates within a region of interest.
        
        Args:
            image: Full image
            roi_bbox: Bounding box of region of interest [x1, y1, x2, y2]
            
        Returns:
            List of plate detections with adjusted coordinates
        """
        x1, y1, x2, y2 = roi_bbox
        roi = image[y1:y2, x1:x2]
        
        detections = self.detect(roi)
        
        # Adjust coordinates to full image space
        for det in detections:
            det['bbox'][0] += x1
            det['bbox'][1] += y1
            det['bbox'][2] += x1
            det['bbox'][3] += y1
        
        return detections
    
    def get_best_plate(self, detections: List[dict]) -> Optional[dict]:
        """
        Get the plate with highest confidence.
        
        Args:
            detections: List of plate detections
            
        Returns:
            Best detection or None if no detections
        """
        if not detections:
            return None
        
        best = max(detections, key=lambda d: d['confidence'])
        return best
    
    def crop_plate(self, image: np.ndarray, bbox: List[int], 
                   padding: int = 5) -> np.ndarray:
        """
        Crop license plate from image with optional padding.
        
        Args:
            image: Input image
            bbox: Plate bounding box [x1, y1, x2, y2]
            padding: Padding pixels around the plate
            
        Returns:
            Cropped plate image
        """
        h, w = image.shape[:2]
        x1, y1, x2, y2 = bbox
        
        # Add padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        return image[y1:y2, x1:x2]
    
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
            
            # Draw bounding box
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Draw label
            label = f"Plate: {confidence:.2f}"
            cv2.putText(img_copy, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        return img_copy
