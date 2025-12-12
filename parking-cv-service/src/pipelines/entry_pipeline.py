"""
Entry pipeline for vehicle entry processing.
"""
import cv2
import numpy as np
from typing import Optional, Dict
import logging
from datetime import datetime

from ..models import VehicleDetector, PlateDetector, PlateOCR
from ..clients.backend_client import BackendClient
from ..config import Config

logger = logging.getLogger(__name__)


class EntryPipeline:
    """Pipeline for processing vehicle entries."""
    
    def __init__(self, config: Config):
        """
        Initialize the entry pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Initialize components
        self.vehicle_detector = VehicleDetector(
            config.VEHICLE_MODEL_PATH,
            config.VEHICLE_CONFIDENCE_THRESHOLD
        )
        self.plate_detector = PlateDetector(
            config.PLATE_MODEL_PATH,
            config.PLATE_CONFIDENCE_THRESHOLD
        )
        self.plate_ocr = PlateOCR(
            config.OCR_LANGUAGES,
            config.OCR_CONFIDENCE_THRESHOLD
        )
        self.backend_client = BackendClient(config.BACKEND_URL, config.API_KEY)
        
        self.frame_count = 0
        self.last_processed_plate = None
        self.last_processed_time = None
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Process a single frame for vehicle entry.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processing result dict or None
        """
        self.frame_count += 1
        
        # Skip frames for performance
        if self.frame_count % self.config.FRAME_SKIP != 0:
            return None
        
        logger.debug(f"Processing frame {self.frame_count}")
        
        # Step 1: Detect vehicles
        vehicle_detections = self.vehicle_detector.detect(frame)
        
        if not vehicle_detections:
            logger.debug("No vehicles detected")
            return None
        
        # Get the largest vehicle (closest to camera)
        vehicle = self.vehicle_detector.get_largest_vehicle(vehicle_detections)
        logger.info(f"Detected {vehicle['class_name']} with confidence {vehicle['confidence']:.2f}")
        
        # Step 2: Detect license plate in vehicle ROI
        plate_detections = self.plate_detector.detect_in_roi(frame, vehicle['bbox'])
        
        if not plate_detections:
            logger.debug("No license plates detected")
            return None
        
        # Get best plate
        plate = self.plate_detector.get_best_plate(plate_detections)
        logger.info(f"Detected license plate with confidence {plate['confidence']:.2f}")
        
        # Step 3: Extract plate image and perform OCR
        plate_image = self.plate_detector.crop_plate(frame, plate['bbox'])
        plate_text = self.plate_ocr.read_with_multiple_attempts(plate_image)
        
        if not plate_text:
            logger.warning("Failed to read plate text")
            return None
        
        # Validate plate format
        if not self.plate_ocr.validate_plate_format(plate_text):
            logger.warning(f"Invalid plate format: {plate_text}")
            return None
        
        # Check for duplicate processing (same plate within time window)
        current_time = datetime.now()
        if (self.last_processed_plate == plate_text and 
            self.last_processed_time and 
            (current_time - self.last_processed_time).seconds < 10):
            logger.debug(f"Skipping duplicate plate: {plate_text}")
            return None
        
        # Update last processed
        self.last_processed_plate = plate_text
        self.last_processed_time = current_time
        
        logger.info(f"Successfully processed entry for plate: {plate_text}")
        
        # Prepare result
        result = {
            'plate_number': plate_text,
            'vehicle_type': vehicle['class_name'],
            'vehicle_confidence': vehicle['confidence'],
            'plate_confidence': plate['confidence'],
            'timestamp': current_time.isoformat(),
            'frame': frame,
            'vehicle_bbox': vehicle['bbox'],
            'plate_bbox': plate['bbox'],
            'plate_image': plate_image
        }
        
        # Step 4: Send to backend
        try:
            response = self.backend_client.register_entry(
                plate_number=plate_text,
                vehicle_type=vehicle['class_name'],
                timestamp=current_time.isoformat(),
                confidence=plate['confidence']
            )
            result['backend_response'] = response
            logger.info(f"Entry registered successfully: {response}")
        except Exception as e:
            logger.error(f"Failed to register entry: {e}")
            result['backend_error'] = str(e)
        
        return result
    
    def run(self, camera_source: str = None, display: bool = True):
        """
        Run the entry pipeline continuously.
        
        Args:
            camera_source: Camera source (URL or device index)
            display: Whether to display the video feed
        """
        if camera_source is None:
            camera_source = self.config.ENTRY_CAMERA_URL
        
        # Try to convert to int if it's a device index
        try:
            camera_source = int(camera_source)
        except ValueError:
            pass
        
        logger.info(f"Starting entry pipeline with camera: {camera_source}")
        
        cap = cv2.VideoCapture(camera_source)
        
        if not cap.isOpened():
            logger.error(f"Failed to open camera: {camera_source}")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                # Process frame
                result = self.process_frame(frame)
                
                # Display if enabled
                if display:
                    display_frame = frame.copy()
                    
                    if result:
                        # Draw detections
                        cv2.rectangle(display_frame, 
                                    (result['vehicle_bbox'][0], result['vehicle_bbox'][1]),
                                    (result['vehicle_bbox'][2], result['vehicle_bbox'][3]),
                                    (0, 255, 0), 2)
                        cv2.rectangle(display_frame,
                                    (result['plate_bbox'][0], result['plate_bbox'][1]),
                                    (result['plate_bbox'][2], result['plate_bbox'][3]),
                                    (255, 0, 0), 2)
                        
                        # Draw plate text
                        cv2.putText(display_frame, result['plate_number'],
                                  (result['plate_bbox'][0], result['plate_bbox'][1] - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    
                    cv2.imshow('Entry Pipeline', display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        finally:
            cap.release()
            if display:
                cv2.destroyAllWindows()
            logger.info("Entry pipeline stopped")
