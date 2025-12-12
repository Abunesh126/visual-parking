"""Automatic Number Plate Recognition (ANPR) Module

Handles license plate detection and recognition using EasyOCR.
Extracts license plate text from detected vehicles for tracking.
"""

import cv2
import numpy as np
import easyocr
import re
from typing import Optional, List, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlateDetection:
    """License plate recognition result"""
    plate_text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    preprocessed_text: str  # Cleaned plate text
    timestamp: datetime

class LicensePlateRecognizer:
    """EasyOCR-based license plate recognizer"""
    
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False):
        """
        Initialize ANPR system
        
        Args:
            languages: List of languages for OCR
            gpu: Use GPU acceleration if available
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        
        # Initialize OCR reader
        self._init_reader()
        
        # Regex pattern for license plate validation
        # Adjust pattern based on your country's plate format
        self.plate_patterns = [
            r'^[A-Z]{1,3}\s?\d{1,4}\s?[A-Z]{0,3}$',  # General pattern
            r'^\d{1,2}\s?[A-Z]{1,3}\s?\d{1,4}$',     # Number-letter-number
            r'^[A-Z]{2}\s?\d{2}\s?[A-Z]{1,3}\s?\d{1,4}$'  # State-code format
        ]
    
    def _init_reader(self):
        """Initialize EasyOCR reader"""
        try:
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            logger.info(f"EasyOCR initialized with languages: {self.languages}")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise
    
    def detect_plate(self, vehicle_roi: np.ndarray) -> Optional[PlateDetection]:
        """
        Detect and recognize license plate in vehicle ROI
        
        Args:
            vehicle_roi: Cropped image containing vehicle
            
        Returns:
            PlateDetection object if plate found, None otherwise
        """
        if self.reader is None:
            return None
            
        try:
            # Preprocess image for better OCR
            processed_roi = self._preprocess_image(vehicle_roi)
            
            # Run OCR
            results = self.reader.readtext(processed_roi)
            
            # Find best plate candidate
            best_plate = self._find_best_plate(results)
            
            if best_plate:
                plate_text, confidence, bbox = best_plate
                
                # Clean and validate plate text
                cleaned_text = self._clean_plate_text(plate_text)
                
                if self._validate_plate_text(cleaned_text):
                    return PlateDetection(
                        plate_text=plate_text,
                        confidence=confidence,
                        bbox=bbox,
                        preprocessed_text=cleaned_text,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Plate detection failed: {e}")
            
        return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def _find_best_plate(self, ocr_results: List) -> Optional[Tuple[str, float, Tuple]]:
        """
        Find the best license plate candidate from OCR results
        
        Args:
            ocr_results: EasyOCR results
            
        Returns:
            Best plate (text, confidence, bbox) or None
        """
        if not ocr_results:
            return None
            
        # Sort results by confidence and text length
        candidates = []
        
        for detection in ocr_results:
            bbox, text, confidence = detection
            
            # Filter by confidence threshold
            if confidence > 0.5:
                # Convert bbox format
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                x, y, w, h = (min(x_coords), min(y_coords), 
                            max(x_coords) - min(x_coords), 
                            max(y_coords) - min(y_coords))
                
                candidates.append((text, confidence, (x, y, w, h)))
        
        if not candidates:
            return None
            
        # Sort by confidence and return best
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0]
    
    def _clean_plate_text(self, text: str) -> str:
        """
        Clean and normalize license plate text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned plate text
        """
        # Remove non-alphanumeric characters except spaces
        cleaned = re.sub(r'[^A-Za-z0-9\s]', '', text)
        
        # Convert to uppercase
        cleaned = cleaned.upper()
        
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        
        return cleaned
    
    def _validate_plate_text(self, text: str) -> bool:
        """
        Validate license plate text against known patterns
        
        Args:
            text: Cleaned plate text
            
        Returns:
            True if valid plate format
        """
        if not text or len(text) < 4:
            return False
            
        # Check against regex patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
                
        # Basic validation: must have both letters and numbers
        has_letter = any(c.isalpha() for c in text)
        has_number = any(c.isdigit() for c in text)
        
        return has_letter and has_number
    
    def extract_plate_from_vehicle(self, frame: np.ndarray, 
                                 vehicle_bbox: Tuple[int, int, int, int]) -> Optional[PlateDetection]:
        """
        Extract license plate from detected vehicle bounding box
        
        Args:
            frame: Full image frame
            vehicle_bbox: Vehicle bounding box (x, y, w, h)
            
        Returns:
            PlateDetection if found, None otherwise
        """
        x, y, w, h = vehicle_bbox
        
        # Crop vehicle region with some padding
        padding = 20
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        
        vehicle_roi = frame[y1:y2, x1:x2]
        
        if vehicle_roi.size == 0:
            return None
            
        return self.detect_plate(vehicle_roi)
    
    def draw_plate_detection(self, frame: np.ndarray, 
                           plate_detection: PlateDetection,
                           vehicle_offset: Tuple[int, int] = (0, 0)) -> np.ndarray:
        """
        Draw license plate detection on frame
        
        Args:
            frame: Image frame
            plate_detection: Plate detection result
            vehicle_offset: Offset for vehicle ROI position
            
        Returns:
            Frame with drawn plate detection
        """
        result_frame = frame.copy()
        
        x, y, w, h = plate_detection.bbox
        # Adjust coordinates if this is within a vehicle ROI
        x += vehicle_offset[0]
        y += vehicle_offset[1]
        
        # Draw plate bounding box
        cv2.rectangle(result_frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        
        # Draw plate text
        label = f"{plate_detection.preprocessed_text} ({plate_detection.confidence:.2f})"
        cv2.putText(result_frame, label, (x, y - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        return result_frame
    
    def get_reader_info(self) -> dict:
        """Get ANPR reader information"""
        return {
            "languages": self.languages,
            "gpu_enabled": self.gpu,
            "reader_initialized": self.reader is not None,
            "supported_patterns": len(self.plate_patterns)
        }