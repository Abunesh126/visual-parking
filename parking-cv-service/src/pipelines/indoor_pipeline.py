"""
Indoor pipeline for parking spot monitoring.
"""
import cv2
import numpy as np
from typing import Optional, Dict, List
import logging
from datetime import datetime

from ..models import VehicleDetector
from ..clients.backend_client import BackendClient
from ..config import Config

logger = logging.getLogger(__name__)


class IndoorPipeline:
    """Pipeline for monitoring indoor parking spots."""
    
    def __init__(self, config: Config, parking_spots: Optional[List[Dict]] = None):
        """
        Initialize the indoor pipeline.
        
        Args:
            config: Configuration object
            parking_spots: List of parking spot definitions (optional)
        """
        self.config = config
        
        # Initialize components
        self.vehicle_detector = VehicleDetector(
            config.VEHICLE_MODEL_PATH,
            config.VEHICLE_CONFIDENCE_THRESHOLD
        )
        self.backend_client = BackendClient(config.BACKEND_URL, config.API_KEY)
        
        # Parking spots configuration
        # Format: [{'id': 'A1', 'bbox': [x1, y1, x2, y2]}, ...]
        self.parking_spots = parking_spots or []
        self.spot_states = {}  # Track occupancy state
        
        self.frame_count = 0
    
    def set_parking_spots(self, spots: List[Dict]):
        """
        Set or update parking spot definitions.
        
        Args:
            spots: List of parking spot definitions
        """
        self.parking_spots = spots
        self.spot_states = {spot['id']: False for spot in spots}
        logger.info(f"Configured {len(spots)} parking spots")
    
    def is_spot_occupied(self, frame: np.ndarray, spot_bbox: List[int]) -> bool:
        """
        Check if a parking spot is occupied.
        
        Args:
            frame: Input frame
            spot_bbox: Bounding box of parking spot [x1, y1, x2, y2]
            
        Returns:
            True if occupied, False otherwise
        """
        # Extract spot ROI
        x1, y1, x2, y2 = spot_bbox
        spot_roi = frame[y1:y2, x1:x2]
        
        # Detect vehicles in spot
        detections = self.vehicle_detector.detect(spot_roi)
        
        # Consider occupied if any vehicle detected with sufficient overlap
        if detections:
            for det in detections:
                # Calculate overlap with spot (simplified)
                det_area = self.vehicle_detector._bbox_area(det['bbox'])
                spot_area = (x2 - x1) * (y2 - y1)
                
                # If detection covers significant portion of spot, it's occupied
                if det_area > spot_area * 0.3:
                    return True
        
        return False
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Process a single frame for parking spot monitoring.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processing result dict or None
        """
        self.frame_count += 1
        
        # Skip frames for performance
        if self.frame_count % self.config.FRAME_SKIP != 0:
            return None
        
        if not self.parking_spots:
            logger.warning("No parking spots configured")
            return None
        
        logger.debug(f"Processing frame {self.frame_count}")
        
        # Check each parking spot
        occupancy_changes = []
        current_states = {}
        
        for spot in self.parking_spots:
            spot_id = spot['id']
            spot_bbox = spot['bbox']
            
            # Check occupancy
            is_occupied = self.is_spot_occupied(frame, spot_bbox)
            current_states[spot_id] = is_occupied
            
            # Detect state change
            previous_state = self.spot_states.get(spot_id, False)
            if is_occupied != previous_state:
                logger.info(f"Spot {spot_id} state changed: {previous_state} -> {is_occupied}")
                occupancy_changes.append({
                    'spot_id': spot_id,
                    'occupied': is_occupied,
                    'timestamp': datetime.now().isoformat()
                })
                self.spot_states[spot_id] = is_occupied
        
        # Prepare result
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_spots': len(self.parking_spots),
            'occupied_spots': sum(current_states.values()),
            'available_spots': len(self.parking_spots) - sum(current_states.values()),
            'spot_states': current_states,
            'occupancy_changes': occupancy_changes,
            'frame': frame
        }
        
        # Send updates to backend if there are changes
        if occupancy_changes:
            try:
                response = self.backend_client.update_parking_status(
                    total_spots=result['total_spots'],
                    occupied_spots=result['occupied_spots'],
                    available_spots=result['available_spots'],
                    changes=occupancy_changes
                )
                result['backend_response'] = response
                logger.info(f"Parking status updated: {response}")
            except Exception as e:
                logger.error(f"Failed to update parking status: {e}")
                result['backend_error'] = str(e)
        
        return result
    
    def draw_parking_spots(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw parking spots on frame with occupancy status.
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with drawn parking spots
        """
        display_frame = frame.copy()
        
        for spot in self.parking_spots:
            spot_id = spot['id']
            x1, y1, x2, y2 = spot['bbox']
            is_occupied = self.spot_states.get(spot_id, False)
            
            # Color: red if occupied, green if available
            color = (0, 0, 255) if is_occupied else (0, 255, 0)
            
            # Draw rectangle
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            status = "OCCUPIED" if is_occupied else "AVAILABLE"
            label = f"{spot_id}: {status}"
            cv2.putText(display_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw summary
        total = len(self.parking_spots)
        occupied = sum(self.spot_states.values())
        available = total - occupied
        summary = f"Total: {total} | Occupied: {occupied} | Available: {available}"
        cv2.putText(display_frame, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return display_frame
    
    def run(self, camera_source: str = None, display: bool = True):
        """
        Run the indoor pipeline continuously.
        
        Args:
            camera_source: Camera source (URL or device index)
            display: Whether to display the video feed
        """
        if camera_source is None:
            camera_source = self.config.INDOOR_CAMERA_URL
        
        # Try to convert to int if it's a device index
        try:
            camera_source = int(camera_source)
        except ValueError:
            pass
        
        logger.info(f"Starting indoor pipeline with camera: {camera_source}")
        
        if not self.parking_spots:
            logger.warning("No parking spots configured. Use set_parking_spots() first.")
        
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
                    display_frame = self.draw_parking_spots(frame)
                    cv2.imshow('Indoor Pipeline', display_frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        finally:
            cap.release()
            if display:
                cv2.destroyAllWindows()
            logger.info("Indoor pipeline stopped")
