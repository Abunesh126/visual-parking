"""Camera Manager for Mall Parking System

Manages multiple camera streams (entry, exit, indoor monitoring) and
coordinates real-time processing with vehicle detection and ANPR.
"""

import cv2
import threading
import time
from typing import Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty
import logging

from .detector import VehicleDetector, Detection
from .anpr import LicensePlateRecognizer, PlateDetection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CameraStream:
    """Camera stream configuration"""
    camera_id: int
    camera_code: str
    rtsp_url: str
    role: str  # ENTRY, EXIT, INDOOR
    floor_id: Optional[int] = None
    is_active: bool = True
    fps: int = 30
    
class CameraManager:
    """Manages multiple camera streams for mall parking system"""
    
    def __init__(self, vehicle_detector: VehicleDetector, 
                 plate_recognizer: LicensePlateRecognizer):
        """
        Initialize camera manager
        
        Args:
            vehicle_detector: Vehicle detection instance
            plate_recognizer: License plate recognition instance
        """
        self.vehicle_detector = vehicle_detector
        self.plate_recognizer = plate_recognizer
        
        # Camera management
        self.cameras: Dict[int, CameraStream] = {}
        self.capture_objects: Dict[int, cv2.VideoCapture] = {}
        self.processing_threads: Dict[int, threading.Thread] = {}
        self.stop_flags: Dict[int, threading.Event] = {}
        
        # Detection queues for each camera
        self.detection_queues: Dict[int, Queue] = {}
        
        # Callbacks for different camera roles
        self.entry_callback: Optional[Callable] = None
        self.exit_callback: Optional[Callable] = None
        self.occupancy_callback: Optional[Callable] = None
        
        # Statistics
        self.frame_counts: Dict[int, int] = {}
        self.last_detection_times: Dict[int, datetime] = {}
        
        self.is_running = False
        
    def add_camera(self, camera_stream: CameraStream):
        """
        Add a camera to the management system
        
        Args:
            camera_stream: Camera configuration
        """
        camera_id = camera_stream.camera_id
        self.cameras[camera_id] = camera_stream
        self.detection_queues[camera_id] = Queue(maxsize=100)
        self.frame_counts[camera_id] = 0
        
        logger.info(f"Added camera {camera_stream.camera_code} (ID: {camera_id})")
    
    def remove_camera(self, camera_id: int):
        """Remove camera from management"""
        if camera_id in self.cameras:
            self.stop_camera(camera_id)
            del self.cameras[camera_id]
            del self.detection_queues[camera_id]
            if camera_id in self.frame_counts:
                del self.frame_counts[camera_id]
            logger.info(f"Removed camera ID: {camera_id}")
    
    def set_entry_callback(self, callback: Callable):
        """Set callback for entry gate detections"""
        self.entry_callback = callback
    
    def set_exit_callback(self, callback: Callable):
        """Set callback for exit gate detections"""
        self.exit_callback = callback
        
    def set_occupancy_callback(self, callback: Callable):
        """Set callback for slot occupancy changes"""
        self.occupancy_callback = callback
    
    def start_all_cameras(self):
        """Start processing for all cameras"""
        self.is_running = True
        
        for camera_id, camera_stream in self.cameras.items():
            if camera_stream.is_active:
                self.start_camera(camera_id)
                
        logger.info(f"Started {len(self.cameras)} cameras")
    
    def start_camera(self, camera_id: int):
        """Start processing for a specific camera"""
        if camera_id not in self.cameras:
            logger.error(f"Camera {camera_id} not found")
            return
            
        camera_stream = self.cameras[camera_id]
        
        try:
            # Initialize video capture
            if camera_stream.rtsp_url.startswith('rtsp://'):
                cap = cv2.VideoCapture(camera_stream.rtsp_url)
            else:
                # For testing with webcam or video file
                cap = cv2.VideoCapture(int(camera_stream.rtsp_url))
                
            if not cap.isOpened():
                logger.error(f"Failed to open camera {camera_stream.camera_code}")
                return
                
            self.capture_objects[camera_id] = cap
            
            # Create stop flag
            stop_flag = threading.Event()
            self.stop_flags[camera_id] = stop_flag
            
            # Start processing thread
            thread = threading.Thread(
                target=self._process_camera_stream,
                args=(camera_id, cap, stop_flag),
                daemon=True
            )
            thread.start()
            self.processing_threads[camera_id] = thread
            
            logger.info(f"Started camera {camera_stream.camera_code}")
            
        except Exception as e:
            logger.error(f"Failed to start camera {camera_id}: {e}")
    
    def stop_camera(self, camera_id: int):
        """Stop processing for a specific camera"""
        if camera_id in self.stop_flags:
            self.stop_flags[camera_id].set()
            
        if camera_id in self.processing_threads:
            self.processing_threads[camera_id].join(timeout=2)
            del self.processing_threads[camera_id]
            
        if camera_id in self.capture_objects:
            self.capture_objects[camera_id].release()
            del self.capture_objects[camera_id]
            
        if camera_id in self.stop_flags:
            del self.stop_flags[camera_id]
            
        logger.info(f"Stopped camera ID: {camera_id}")
    
    def stop_all_cameras(self):
        """Stop all cameras"""
        self.is_running = False
        
        camera_ids = list(self.cameras.keys())
        for camera_id in camera_ids:
            self.stop_camera(camera_id)
            
        logger.info("Stopped all cameras")
    
    def _process_camera_stream(self, camera_id: int, cap: cv2.VideoCapture, 
                              stop_flag: threading.Event):
        """Process individual camera stream"""
        camera_stream = self.cameras[camera_id]
        
        # Calculate frame skip for desired FPS
        target_fps = camera_stream.fps
        frame_interval = 1.0 / target_fps
        last_frame_time = 0
        
        while not stop_flag.is_set():
            try:
                current_time = time.time()
                
                # Skip frames to maintain target FPS
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue
                    
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera_id}")
                    continue
                    
                last_frame_time = current_time
                self.frame_counts[camera_id] += 1
                
                # Process frame based on camera role
                self._process_frame(camera_id, frame)
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error processing camera {camera_id}: {e}")
                time.sleep(1)
    
    def _process_frame(self, camera_id: int, frame):
        """Process a single frame from camera"""
        camera_stream = self.cameras[camera_id]
        
        # Detect vehicles in frame
        detections = self.vehicle_detector.detect_vehicles(frame)
        
        if detections:
            self.last_detection_times[camera_id] = datetime.now()
            
            for detection in detections:
                # Try to recognize license plate
                plate_detection = self.plate_recognizer.extract_plate_from_vehicle(
                    frame, detection.bbox
                )
                
                # Handle detection based on camera role
                if camera_stream.role == "ENTRY" and self.entry_callback:
                    self._handle_entry_detection(camera_id, detection, plate_detection)
                elif camera_stream.role == "EXIT" and self.exit_callback:
                    self._handle_exit_detection(camera_id, detection, plate_detection)
                elif camera_stream.role == "INDOOR" and self.occupancy_callback:
                    self._handle_occupancy_detection(camera_id, detection, plate_detection)
    
    def _handle_entry_detection(self, camera_id: int, vehicle: Detection, 
                              plate: Optional[PlateDetection]):
        """Handle vehicle detection at entry gate"""
        try:
            self.entry_callback({
                'camera_id': camera_id,
                'vehicle_type': vehicle.class_name,
                'confidence': vehicle.confidence,
                'license_plate': plate.preprocessed_text if plate else None,
                'plate_confidence': plate.confidence if plate else 0.0,
                'timestamp': vehicle.timestamp
            })
        except Exception as e:
            logger.error(f"Entry callback failed: {e}")
    
    def _handle_exit_detection(self, camera_id: int, vehicle: Detection,
                             plate: Optional[PlateDetection]):
        """Handle vehicle detection at exit gate"""
        try:
            self.exit_callback({
                'camera_id': camera_id,
                'vehicle_type': vehicle.class_name,
                'confidence': vehicle.confidence,
                'license_plate': plate.preprocessed_text if plate else None,
                'plate_confidence': plate.confidence if plate else 0.0,
                'timestamp': vehicle.timestamp
            })
        except Exception as e:
            logger.error(f"Exit callback failed: {e}")
    
    def _handle_occupancy_detection(self, camera_id: int, vehicle: Detection,
                                  plate: Optional[PlateDetection]):
        """Handle vehicle detection for slot occupancy"""
        try:
            self.occupancy_callback({
                'camera_id': camera_id,
                'vehicle_type': vehicle.class_name,
                'confidence': vehicle.confidence,
                'license_plate': plate.preprocessed_text if plate else None,
                'plate_confidence': plate.confidence if plate else 0.0,
                'position': vehicle.center_point,
                'timestamp': vehicle.timestamp
            })
        except Exception as e:
            logger.error(f"Occupancy callback failed: {e}")
    
    def get_camera_status(self) -> Dict:
        """Get status of all cameras"""
        status = {}
        
        for camera_id, camera_stream in self.cameras.items():
            status[camera_id] = {
                'camera_code': camera_stream.camera_code,
                'role': camera_stream.role,
                'is_active': camera_stream.is_active,
                'is_running': camera_id in self.processing_threads,
                'frames_processed': self.frame_counts.get(camera_id, 0),
                'last_detection': self.last_detection_times.get(camera_id),
                'rtsp_url': camera_stream.rtsp_url
            }
            
        return status
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        total_cameras = len(self.cameras)
        active_cameras = sum(1 for c in self.cameras.values() if c.is_active)
        running_cameras = len(self.processing_threads)
        total_frames = sum(self.frame_counts.values())
        
        return {
            'total_cameras': total_cameras,
            'active_cameras': active_cameras,
            'running_cameras': running_cameras,
            'total_frames_processed': total_frames,
            'is_system_running': self.is_running
        }