"""Slot Occupancy Detection Module

Detects parking slot occupancy using Region of Interest (ROI) analysis
with computer vision. Each parking slot has predefined ROI coordinates.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SlotROI:
    """Parking slot Region of Interest"""
    slot_id: int
    slot_code: str
    coordinates: Tuple[int, int, int, int]  # (x, y, width, height)
    vehicle_type: str  # CAR or BIKE
    camera_id: int
    
@dataclass 
class SlotStatus:
    """Current status of a parking slot"""
    slot_id: int
    is_occupied: bool
    confidence: float
    license_plate: Optional[str] = None
    vehicle_type: Optional[str] = None
    last_updated: datetime = None
    
class SlotOccupancyDetector:
    """Detects parking slot occupancy using ROI analysis"""
    
    def __init__(self, motion_threshold: float = 0.3, 
                 occupancy_threshold: float = 0.4):
        """
        Initialize slot occupancy detector
        
        Args:
            motion_threshold: Minimum motion to detect vehicle
            occupancy_threshold: Minimum area ratio for occupancy
        """
        self.motion_threshold = motion_threshold
        self.occupancy_threshold = occupancy_threshold
        
        # ROI definitions for each camera
        self.camera_rois: Dict[int, List[SlotROI]] = {}
        
        # Background subtractors for motion detection
        self.bg_subtractors: Dict[int, cv2.BackgroundSubtractor] = {}
        
        # Previous slot statuses for change detection
        self.previous_statuses: Dict[int, SlotStatus] = {}
        
        # Initialize slot layout based on mall configuration
        self._initialize_slot_layout()
        
    def _initialize_slot_layout(self):
        """
        Initialize parking slot layout for mall system
        
        Floor A & B layout:
        - 20 car slots per floor (4 slots per camera = 5 car cameras per floor)
        - 16 bike slots per floor (8 slots per camera = 2 bike cameras per floor)
        """
        # This would typically be loaded from database or config file
        # For now, we'll create a template layout
        
        camera_id = 1  # Starting camera ID for indoor cameras
        
        for floor in ['A', 'B']:
            # Car slot cameras (5 per floor)
            for car_cam in range(1, 6):
                camera_code = f"{floor}_CAR_{car_cam:02d}"
                rois = self._generate_car_slot_rois(camera_id, floor, car_cam)
                self.camera_rois[camera_id] = rois
                
                # Initialize background subtractor
                self.bg_subtractors[camera_id] = cv2.createBackgroundSubtractorMOG2(
                    detectShadows=True
                )
                
                camera_id += 1
                
            # Bike slot cameras (2 per floor) 
            for bike_cam in range(1, 3):
                camera_code = f"{floor}_BIKE_{bike_cam:02d}"
                rois = self._generate_bike_slot_rois(camera_id, floor, bike_cam)
                self.camera_rois[camera_id] = rois
                
                # Initialize background subtractor
                self.bg_subtractors[camera_id] = cv2.createBackgroundSubtractorMOG2(
                    detectShadows=True
                )
                
                camera_id += 1
    
    def _generate_car_slot_rois(self, camera_id: int, floor: str, 
                               cam_num: int) -> List[SlotROI]:
        """
        Generate ROI coordinates for car slots
        
        Args:
            camera_id: Camera identifier
            floor: Floor name (A or B)
            cam_num: Camera number on floor
            
        Returns:
            List of SlotROI objects for this camera
        """
        rois = []
        
        # Calculate which slots this camera covers (4 car slots per camera)
        start_slot = (cam_num - 1) * 4 + 1
        end_slot = start_slot + 4
        
        # Template ROI layout for car slots (adjust based on actual camera view)
        slot_width = 120
        slot_height = 200
        start_x = 50
        start_y = 100
        spacing = 130
        
        for i, slot_num in enumerate(range(start_slot, end_slot)):
            slot_code = f"{floor}-C-{slot_num:02d}"
            
            # Calculate ROI coordinates
            x = start_x + i * spacing
            y = start_y
            
            roi = SlotROI(
                slot_id=self._calculate_slot_id(floor, 'CAR', slot_num),
                slot_code=slot_code,
                coordinates=(x, y, slot_width, slot_height),
                vehicle_type='CAR',
                camera_id=camera_id
            )
            rois.append(roi)
            
        return rois
    
    def _generate_bike_slot_rois(self, camera_id: int, floor: str,
                               cam_num: int) -> List[SlotROI]:
        """
        Generate ROI coordinates for bike slots
        
        Args:
            camera_id: Camera identifier
            floor: Floor name (A or B)
            cam_num: Camera number on floor
            
        Returns:
            List of SlotROI objects for this camera
        """
        rois = []
        
        # Calculate which slots this camera covers (8 bike slots per camera)
        start_slot = (cam_num - 1) * 8 + 1
        end_slot = start_slot + 8
        
        # Template ROI layout for bike slots (smaller than car slots)
        slot_width = 60
        slot_height = 120
        start_x = 30
        start_y = 80
        spacing = 70
        
        for i, slot_num in enumerate(range(start_slot, end_slot)):
            slot_code = f"{floor}-B-{slot_num:02d}"
            
            # Calculate ROI coordinates (2 rows of 4)
            row = i // 4
            col = i % 4
            
            x = start_x + col * spacing
            y = start_y + row * (slot_height + 20)
            
            roi = SlotROI(
                slot_id=self._calculate_slot_id(floor, 'BIKE', slot_num),
                slot_code=slot_code,
                coordinates=(x, y, slot_width, slot_height),
                vehicle_type='BIKE',
                camera_id=camera_id
            )
            rois.append(roi)
            
        return rois
    
    def _calculate_slot_id(self, floor: str, vehicle_type: str, slot_num: int) -> int:
        """
        Calculate unique slot ID based on floor, type, and number
        
        Args:
            floor: 'A' or 'B'
            vehicle_type: 'CAR' or 'BIKE'
            slot_num: Slot number within type
            
        Returns:
            Unique slot ID
        """
        floor_offset = 0 if floor == 'A' else 1000
        type_offset = 0 if vehicle_type == 'CAR' else 100
        
        return floor_offset + type_offset + slot_num
    
    def detect_slot_occupancy(self, camera_id: int, 
                            frame: np.ndarray) -> List[SlotStatus]:
        """
        Detect occupancy status for all slots monitored by a camera
        
        Args:
            camera_id: Camera identifier
            frame: Camera frame
            
        Returns:
            List of slot statuses
        """
        if camera_id not in self.camera_rois:
            return []
            
        slot_statuses = []
        
        # Apply background subtraction
        bg_mask = self._apply_background_subtraction(camera_id, frame)
        
        # Check each slot ROI
        for slot_roi in self.camera_rois[camera_id]:
            status = self._check_slot_occupancy(frame, bg_mask, slot_roi)
            slot_statuses.append(status)
            
            # Track status changes
            self._track_status_change(status)
            
        return slot_statuses
    
    def _apply_background_subtraction(self, camera_id: int, 
                                    frame: np.ndarray) -> np.ndarray:
        """
        Apply background subtraction to detect motion/changes
        
        Args:
            camera_id: Camera identifier
            frame: Input frame
            
        Returns:
            Background subtraction mask
        """
        if camera_id not in self.bg_subtractors:
            return np.zeros(frame.shape[:2], dtype=np.uint8)
            
        bg_subtractor = self.bg_subtractors[camera_id]
        fg_mask = bg_subtractor.apply(frame)
        
        # Clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        return fg_mask
    
    def _check_slot_occupancy(self, frame: np.ndarray, bg_mask: np.ndarray,
                            slot_roi: SlotROI) -> SlotStatus:
        """
        Check occupancy status for a single slot
        
        Args:
            frame: Original frame
            bg_mask: Background subtraction mask
            slot_roi: Slot ROI definition
            
        Returns:
            Slot status
        """
        x, y, w, h = slot_roi.coordinates
        
        # Extract slot region
        slot_region = frame[y:y+h, x:x+w]
        mask_region = bg_mask[y:y+h, x:x+w]
        
        # Calculate occupancy based on multiple factors
        occupancy_score = self._calculate_occupancy_score(slot_region, mask_region)
        
        is_occupied = occupancy_score > self.occupancy_threshold
        
        return SlotStatus(
            slot_id=slot_roi.slot_id,
            is_occupied=is_occupied,
            confidence=occupancy_score,
            last_updated=datetime.now()
        )
    
    def _calculate_occupancy_score(self, slot_region: np.ndarray,
                                 mask_region: np.ndarray) -> float:
        """
        Calculate occupancy confidence score
        
        Args:
            slot_region: Slot image region
            mask_region: Background subtraction mask for slot
            
        Returns:
            Occupancy confidence (0-1)
        """
        if slot_region.size == 0:
            return 0.0
            
        # Calculate various metrics
        
        # 1. Motion/foreground detection score
        motion_pixels = np.sum(mask_region > 0)
        total_pixels = mask_region.size
        motion_score = motion_pixels / total_pixels if total_pixels > 0 else 0
        
        # 2. Edge density (vehicles have more edges)
        gray_slot = cv2.cvtColor(slot_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray_slot, 50, 150)
        edge_score = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
        
        # 3. Color variance (empty slots are usually uniform)
        color_variance = np.var(slot_region)
        normalized_variance = min(color_variance / 1000, 1.0)  # Normalize
        
        # Combine scores with weights
        occupancy_score = (
            0.4 * motion_score +
            0.3 * edge_score +
            0.3 * normalized_variance
        )
        
        return min(occupancy_score, 1.0)
    
    def _track_status_change(self, status: SlotStatus):
        """Track and log slot status changes"""
        slot_id = status.slot_id
        
        if slot_id in self.previous_statuses:
            prev_status = self.previous_statuses[slot_id]
            
            # Check for status change
            if prev_status.is_occupied != status.is_occupied:
                logger.info(
                    f"Slot {slot_id} status changed: "
                    f"{prev_status.is_occupied} → {status.is_occupied} "
                    f"(confidence: {status.confidence:.2f})"
                )
                
        self.previous_statuses[slot_id] = status
    
    def draw_slot_overlays(self, frame: np.ndarray, 
                         camera_id: int,
                         slot_statuses: List[SlotStatus]) -> np.ndarray:
        """
        Draw slot ROI overlays on frame
        
        Args:
            frame: Input frame
            camera_id: Camera identifier
            slot_statuses: Current slot statuses
            
        Returns:
            Frame with overlays
        """
        if camera_id not in self.camera_rois:
            return frame
            
        result_frame = frame.copy()
        
        # Create status lookup
        status_map = {s.slot_id: s for s in slot_statuses}
        
        for slot_roi in self.camera_rois[camera_id]:
            x, y, w, h = slot_roi.coordinates
            slot_status = status_map.get(slot_roi.slot_id)
            
            if slot_status:
                # Choose color based on occupancy
                if slot_status.is_occupied:
                    color = (0, 0, 255)  # Red for occupied
                else:
                    color = (0, 255, 0)  # Green for free
                    
                # Draw rectangle
                cv2.rectangle(result_frame, (x, y), (x+w, y+h), color, 2)
                
                # Draw slot info
                label = f"{slot_roi.slot_code}"
                confidence_label = f"{slot_status.confidence:.2f}"
                
                cv2.putText(result_frame, label, (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.putText(result_frame, confidence_label, (x, y+h+15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return result_frame
    
    def load_roi_config(self, config_path: str):
        """Load ROI configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            self.camera_rois = {}
            for camera_data in config['cameras']:
                camera_id = camera_data['camera_id']
                rois = []
                
                for slot_data in camera_data['slots']:
                    roi = SlotROI(
                        slot_id=slot_data['slot_id'],
                        slot_code=slot_data['slot_code'],
                        coordinates=tuple(slot_data['coordinates']),
                        vehicle_type=slot_data['vehicle_type'],
                        camera_id=camera_id
                    )
                    rois.append(roi)
                    
                self.camera_rois[camera_id] = rois
                
            logger.info(f"Loaded ROI config from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load ROI config: {e}")
    
    def save_roi_config(self, config_path: str):
        """Save current ROI configuration to JSON file"""
        try:
            config = {'cameras': []}
            
            for camera_id, rois in self.camera_rois.items():
                camera_data = {
                    'camera_id': camera_id,
                    'slots': []
                }
                
                for roi in rois:
                    slot_data = {
                        'slot_id': roi.slot_id,
                        'slot_code': roi.slot_code,
                        'coordinates': list(roi.coordinates),
                        'vehicle_type': roi.vehicle_type
                    }
                    camera_data['slots'].append(slot_data)
                    
                config['cameras'].append(camera_data)
                
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Saved ROI config to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save ROI config: {e}")
    
    def get_detector_stats(self) -> Dict:
        """Get occupancy detector statistics"""
        return {
            'total_cameras': len(self.camera_rois),
            'total_slots': sum(len(rois) for rois in self.camera_rois.values()),
            'motion_threshold': self.motion_threshold,
            'occupancy_threshold': self.occupancy_threshold,
            'tracked_slots': len(self.previous_statuses)
        }