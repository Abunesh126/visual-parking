"""
Backend API client for communication with parking management system.
"""
import requests
from typing import Dict, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for communicating with the backend parking management API."""
    
    def __init__(self, base_url: str, api_key: str = ""):
        """
        Initialize the backend client.
        
        Args:
            base_url: Base URL of the backend API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # Set default headers
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def register_entry(self, plate_number: str, vehicle_type: str,
                      timestamp: str, confidence: float,
                      image_data: Optional[str] = None) -> Dict:
        """
        Register a vehicle entry.
        
        Args:
            plate_number: License plate number
            vehicle_type: Type of vehicle (car, motorcycle, etc.)
            timestamp: Entry timestamp (ISO format)
            confidence: Detection confidence score
            image_data: Base64 encoded image (optional)
            
        Returns:
            API response dict
        """
        endpoint = f"{self.base_url}/api/entries"
        
        payload = {
            'plate_number': plate_number,
            'vehicle_type': vehicle_type,
            'timestamp': timestamp,
            'confidence': confidence
        }
        
        if image_data:
            payload['image'] = image_data
        
        try:
            logger.info(f"Registering entry for plate: {plate_number}")
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Entry registered successfully: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register entry: {e}")
            raise
    
    def register_exit(self, plate_number: str, timestamp: str,
                     duration: Optional[int] = None) -> Dict:
        """
        Register a vehicle exit.
        
        Args:
            plate_number: License plate number
            timestamp: Exit timestamp (ISO format)
            duration: Parking duration in minutes (optional)
            
        Returns:
            API response dict
        """
        endpoint = f"{self.base_url}/api/exits"
        
        payload = {
            'plate_number': plate_number,
            'timestamp': timestamp
        }
        
        if duration is not None:
            payload['duration'] = duration
        
        try:
            logger.info(f"Registering exit for plate: {plate_number}")
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Exit registered successfully: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to register exit: {e}")
            raise
    
    def update_parking_status(self, total_spots: int, occupied_spots: int,
                             available_spots: int,
                             changes: Optional[List[Dict]] = None) -> Dict:
        """
        Update parking spot occupancy status.
        
        Args:
            total_spots: Total number of parking spots
            occupied_spots: Number of occupied spots
            available_spots: Number of available spots
            changes: List of spot state changes (optional)
            
        Returns:
            API response dict
        """
        endpoint = f"{self.base_url}/api/parking-status"
        
        payload = {
            'total_spots': total_spots,
            'occupied_spots': occupied_spots,
            'available_spots': available_spots,
            'timestamp': datetime.now().isoformat()
        }
        
        if changes:
            payload['changes'] = changes
        
        try:
            logger.info(f"Updating parking status: {occupied_spots}/{total_spots} occupied")
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Parking status updated successfully: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update parking status: {e}")
            raise
    
    def get_vehicle_info(self, plate_number: str) -> Optional[Dict]:
        """
        Get vehicle information by plate number.
        
        Args:
            plate_number: License plate number
            
        Returns:
            Vehicle info dict or None if not found
        """
        endpoint = f"{self.base_url}/api/vehicles/{plate_number}"
        
        try:
            logger.info(f"Fetching vehicle info for plate: {plate_number}")
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Vehicle info retrieved: {data}")
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Vehicle not found: {plate_number}")
                return None
            logger.error(f"Failed to get vehicle info: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get vehicle info: {e}")
            raise
    
    def get_parking_availability(self) -> Dict:
        """
        Get current parking availability.
        
        Returns:
            Availability info dict
        """
        endpoint = f"{self.base_url}/api/parking-status"
        
        try:
            logger.debug("Fetching parking availability")
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Parking availability: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get parking availability: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if backend API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        endpoint = f"{self.base_url}/api/health"
        
        try:
            response = self.session.get(endpoint, timeout=5)
            response.raise_for_status()
            logger.info("Backend health check: OK")
            return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Backend health check failed: {e}")
            return False
