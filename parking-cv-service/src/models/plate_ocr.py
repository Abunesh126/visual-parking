"""
License plate OCR module using EasyOCR.
"""
import cv2
import numpy as np
import easyocr
from typing import Optional, List
import logging
import re

logger = logging.getLogger(__name__)


class PlateOCR:
    """Performs OCR on license plate images."""
    
    def __init__(self, languages: List[str] = ['en'], 
                 confidence_threshold: float = 0.7):
        """
        Initialize the OCR engine.
        
        Args:
            languages: List of language codes for OCR
            confidence_threshold: Minimum confidence for text detection
        """
        self.languages = languages
        self.confidence_threshold = confidence_threshold
        self.reader = None
        self._load_reader()
    
    def _load_reader(self):
        """Load the EasyOCR reader."""
        try:
            logger.info(f"Loading OCR reader for languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=True)
            logger.info("OCR reader loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load OCR with GPU, falling back to CPU: {e}")
            try:
                self.reader = easyocr.Reader(self.languages, gpu=False)
                logger.info("OCR reader loaded successfully (CPU)")
            except Exception as e:
                logger.error(f"Failed to load OCR reader: {e}")
                raise
    
    def preprocess_plate(self, plate_image: np.ndarray) -> np.ndarray:
        """
        Preprocess plate image for better OCR results.
        
        Args:
            plate_image: Input plate image
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(plate_image.shape) == 3:
            gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_image
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary)
        
        # Resize for better OCR (height = 64 pixels)
        h, w = denoised.shape
        scale = 64 / h
        new_w = int(w * scale)
        resized = cv2.resize(denoised, (new_w, 64), interpolation=cv2.INTER_CUBIC)
        
        return resized
    
    def read_text(self, plate_image: np.ndarray, 
                  preprocess: bool = True) -> Optional[str]:
        """
        Extract text from license plate image.
        
        Args:
            plate_image: Cropped license plate image
            preprocess: Whether to preprocess the image
            
        Returns:
            Extracted text or None if no text found
        """
        if self.reader is None:
            raise RuntimeError("OCR reader not loaded")
        
        try:
            # Preprocess image
            if preprocess:
                processed_image = self.preprocess_plate(plate_image)
            else:
                processed_image = plate_image
            
            # Perform OCR
            results = self.reader.readtext(processed_image)
            
            if not results:
                logger.debug("No text detected in plate image")
                return None
            
            # Filter by confidence and get best result
            valid_results = [
                (text, conf) for (bbox, text, conf) in results 
                if conf >= self.confidence_threshold
            ]
            
            if not valid_results:
                logger.debug("No text met confidence threshold")
                return None
            
            # Get result with highest confidence
            best_text, best_conf = max(valid_results, key=lambda x: x[1])
            
            # Clean the text
            clean_text = self.clean_plate_text(best_text)
            
            logger.info(f"Detected plate text: '{clean_text}' (confidence: {best_conf:.2f})")
            return clean_text
            
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return None
    
    def clean_plate_text(self, text: str) -> str:
        """
        Clean and normalize plate text.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Remove spaces and special characters
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Common OCR corrections
        corrections = {
            'O': '0',  # Letter O to zero (context dependent)
            'I': '1',  # Letter I to one (context dependent)
            'S': '5',  # Letter S to five (context dependent)
            'B': '8',  # Letter B to eight (context dependent)
        }
        
        # Apply corrections (basic heuristic)
        # This is simplified - in production, use more sophisticated logic
        # based on plate format patterns
        
        return text
    
    def read_with_multiple_attempts(self, plate_image: np.ndarray) -> Optional[str]:
        """
        Try multiple preprocessing strategies for OCR.
        
        Args:
            plate_image: License plate image
            
        Returns:
            Best OCR result or None
        """
        attempts = []
        
        # Attempt 1: Standard preprocessing
        result1 = self.read_text(plate_image, preprocess=True)
        if result1:
            attempts.append(result1)
        
        # Attempt 2: No preprocessing
        result2 = self.read_text(plate_image, preprocess=False)
        if result2:
            attempts.append(result2)
        
        # Attempt 3: Enhanced contrast
        enhanced = cv2.convertScaleAbs(plate_image, alpha=1.5, beta=0)
        result3 = self.read_text(enhanced, preprocess=True)
        if result3:
            attempts.append(result3)
        
        # Return most common result or longest one
        if not attempts:
            return None
        
        # Simple heuristic: return longest text
        return max(attempts, key=len)
    
    def validate_plate_format(self, text: str, pattern: Optional[str] = None) -> bool:
        """
        Validate plate text against expected format.
        
        Args:
            text: Plate text to validate
            pattern: Regex pattern for validation (optional)
            
        Returns:
            True if valid, False otherwise
        """
        if not text:
            return False
        
        # Basic validation: 4-8 alphanumeric characters
        if not (4 <= len(text) <= 8):
            return False
        
        # If pattern provided, validate against it
        if pattern:
            return bool(re.match(pattern, text))
        
        # Default: must contain at least one digit and one letter
        has_digit = any(c.isdigit() for c in text)
        has_letter = any(c.isalpha() for c in text)
        
        return has_digit and has_letter
