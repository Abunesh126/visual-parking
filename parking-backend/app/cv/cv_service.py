"""Computer Vision Service Integration

Main service that coordinates CV components with the parking system:
- Manages camera streams and detection processing
- Integrates with entry/exit/occupancy APIs
- Handles real-time vehicle and plate recognition
- Provides CV system monitoring and statistics
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import threading

from .detector import VehicleDetector
from .anpr import LicensePlateRecognizer
from .camera_manager import CameraManager, CameraStream
from .slot_detector import SlotOccupancyDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CVSystemConfig:
    """Computer Vision system configuration"""
    api_base_url: str = "http://localhost:8000/api/v1"
    yolo_model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.6
    plate_confidence_threshold: float = 0.7
    processing_fps: int = 5  # Process every 5th frame
    enable_gpu: bool = False
    
class CVParkingService:
    """Main CV service for mall parking system"""
    
    def __init__(self, config: CVSystemConfig):
        """
        Initialize CV parking service
        
        Args:
            config: CV system configuration
        """
        self.config = config
        
        # Initialize CV components
        self.vehicle_detector = VehicleDetector(
            model_path=config.yolo_model_path,
            confidence_threshold=config.confidence_threshold
        )
        
        self.plate_recognizer = LicensePlateRecognizer(
            languages=['en'],
            gpu=config.enable_gpu
        )
        
        self.camera_manager = CameraManager(
            self.vehicle_detector,
            self.plate_recognizer
        )
        
        self.slot_detector = SlotOccupancyDetector()
        
        # System state
        self.is_running = False
        self.last_api_call = {}
        self.detection_stats = {
            'total_detections': 0,
            'successful_entries': 0,
            'successful_exits': 0,
            'failed_detections': 0,
            'last_reset': datetime.now()
        }
        
        # Rate limiting for API calls
        self.api_cooldown = timedelta(seconds=5)  # Min time between API calls for same plate
        
        self._setup_callbacks()
        
    def _setup_callbacks(self):
        """Setup camera detection callbacks"""
        self.camera_manager.set_entry_callback(self._handle_entry_detection)
        self.camera_manager.set_exit_callback(self._handle_exit_detection)
        self.camera_manager.set_occupancy_callback(self._handle_occupancy_detection)
    
    async def initialize_cameras(self, camera_configs: List[Dict]):
        """
        Initialize camera system with configuration
        
        Args:
            camera_configs: List of camera configuration dicts
        """
        try:
            logger.info(f"Initializing {len(camera_configs)} cameras...")
            
            for camera_config in camera_configs:
                camera_stream = CameraStream(
                    camera_id=camera_config['id'],
                    camera_code=camera_config['code'],
                    rtsp_url=camera_config['rtsp_url'],
                    role=camera_config['role'],
                    floor_id=camera_config.get('floor_id'),
                    fps=camera_config.get('fps', 10)
                )
                
                self.camera_manager.add_camera(camera_stream)
                
            logger.info("Camera initialization completed")
            
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            raise
    
    def start_cv_system(self):
        """
        Start the computer vision processing system
        """
        try:
            logger.info("Starting CV parking system...")
            
            self.is_running = True
            self.camera_manager.start_all_cameras()
            
            logger.info("CV system started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start CV system: {e}")
            self.is_running = False
            raise
    
    def stop_cv_system(self):
        """Stop the computer vision system"""
        try:
            logger.info("Stopping CV parking system...")
            
            self.is_running = False
            self.camera_manager.stop_all_cameras()
            
            logger.info("CV system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping CV system: {e}")
    
    def _handle_entry_detection(self, detection_data: Dict):
        """
        Handle vehicle detection at entry gate
        
        Args:
            detection_data: Detection information from camera
        """
        try:
            license_plate = detection_data.get('license_plate')
            if not license_plate:
                logger.warning("Entry detection without license plate")
                return
            
            # Check rate limiting
            if self._is_rate_limited('entry', license_plate):
                return
            
            # Check confidence threshold
            plate_confidence = detection_data.get('plate_confidence', 0.0)
            if plate_confidence < self.config.plate_confidence_threshold:
                logger.warning(
                    f"Low confidence plate detection: {license_plate} ({plate_confidence:.2f})"
                )
                self.detection_stats['failed_detections'] += 1
                return
            
            # Make async API call to entry endpoint
            asyncio.create_task(
                self._call_entry_api(detection_data)
            )
            
        except Exception as e:
            logger.error(f"Entry detection handling failed: {e}")
    
    def _handle_exit_detection(self, detection_data: Dict):
        """
        Handle vehicle detection at exit gate
        
        Args:
            detection_data: Detection information from camera
        """
        try:
            license_plate = detection_data.get('license_plate')
            if not license_plate:
                logger.warning("Exit detection without license plate")
                return
            
            # Check rate limiting
            if self._is_rate_limited('exit', license_plate):
                return
            
            # Make async API call to exit endpoint
            asyncio.create_task(
                self._call_exit_api(detection_data)
            )
            
        except Exception as e:
            logger.error(f"Exit detection handling failed: {e}")
    
    def _handle_occupancy_detection(self, detection_data: Dict):
        """
        Handle slot occupancy detection from indoor cameras
        
        Args:
            detection_data: Detection information from camera
        """
        try:
            camera_id = detection_data.get('camera_id')
            if not camera_id:
                return
                
            # Process with slot detector
            # This would integrate with slot_detector to update slot statuses
            logger.debug(f"Occupancy detection from camera {camera_id}")
            
        except Exception as e:
            logger.error(f"Occupancy detection handling failed: {e}")
    
    def _is_rate_limited(self, detection_type: str, license_plate: str) -> bool:
        """
        Check if API call should be rate limited
        
        Args:
            detection_type: 'entry' or 'exit'
            license_plate: Vehicle license plate
            
        Returns:
            True if rate limited
        """
        key = f"{detection_type}_{license_plate}"
        last_call = self.last_api_call.get(key)
        
        if last_call and datetime.now() - last_call < self.api_cooldown:
            return True
            
        self.last_api_call[key] = datetime.now()
        return False
    
    async def _call_entry_api(self, detection_data: Dict):
        """Make API call to entry endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.api_base_url}/cv-entry-detection"
                
                async with session.post(url, json=detection_data) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(
                            f"Entry processed: {detection_data['license_plate']} → "
                            f"slot {result.get('assigned_slot')}"
                        )
                        self.detection_stats['successful_entries'] += 1
                    else:
                        error_text = await response.text()
                        logger.error(f"Entry API call failed: {error_text}")
                        self.detection_stats['failed_detections'] += 1
                        
        except Exception as e:
            logger.error(f"Entry API call error: {e}")
            self.detection_stats['failed_detections'] += 1
    
    async def _call_exit_api(self, detection_data: Dict):
        """Make API call to exit endpoint"""
        try:
            license_plate = detection_data['license_plate']
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.api_base_url}/exit-events/license/{license_plate}"
                
                async with session.post(url, json={}) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"Exit processed: {license_plate}, "
                            f"duration: {result.get('parking_duration_minutes', 0)} min"
                        )
                        self.detection_stats['successful_exits'] += 1
                    else:
                        error_text = await response.text()
                        logger.error(f"Exit API call failed: {error_text}")
                        self.detection_stats['failed_detections'] += 1
                        
        except Exception as e:
            logger.error(f"Exit API call error: {e}")
            self.detection_stats['failed_detections'] += 1
    
    def get_system_status(self) -> Dict:
        """Get comprehensive CV system status"""
        camera_status = self.camera_manager.get_camera_status()
        system_stats = self.camera_manager.get_system_stats()
        detector_stats = self.slot_detector.get_detector_stats()
        
        return {
            'cv_system': {
                'is_running': self.is_running,
                'config': {
                    'api_base_url': self.config.api_base_url,
                    'confidence_threshold': self.config.confidence_threshold,
                    'plate_confidence_threshold': self.config.plate_confidence_threshold,
                    'processing_fps': self.config.processing_fps
                }
            },
            'cameras': camera_status,
            'system_stats': system_stats,
            'detector_stats': detector_stats,
            'detection_performance': self.detection_stats,
            'component_status': {
                'vehicle_detector': self.vehicle_detector.get_model_info(),
                'plate_recognizer': self.plate_recognizer.get_reader_info()
            }
        }
    
    def reset_statistics(self):
        """Reset detection statistics"""
        self.detection_stats = {
            'total_detections': 0,
            'successful_entries': 0,
            'successful_exits': 0,
            'failed_detections': 0,
            'last_reset': datetime.now()
        }
        logger.info("Detection statistics reset")

# Convenience function to create and configure CV service
def create_cv_service(api_base_url: str = "http://localhost:8000/api/v1") -> CVParkingService:
    """Create and configure CV parking service"""
    config = CVSystemConfig(api_base_url=api_base_url)
    return CVParkingService(config)