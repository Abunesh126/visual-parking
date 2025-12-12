import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, func, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class CameraRole(str, enum.Enum):
    """Camera roles in the mall parking system"""
    ENTRY = "ENTRY"      # Entry gate camera (1 camera)
    EXIT = "EXIT"        # Exit gate camera (1 camera)
    INDOOR = "INDOOR"    # Indoor monitoring cameras (14 total)

class CameraStatus(str, enum.Enum):
    """Camera operational status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE" 
    MAINTENANCE = "MAINTENANCE"

class Camera(Base):
    """Camera model for mall parking system
    
    Camera layout:
    - 1 entry camera: ENTRY_1
    - 1 exit camera: EXIT_1  
    - Per floor (A/B):
        - Car slots: 5 cameras (every 4 car slots = 1 camera)
        - Bike slots: 2 cameras (every 8 bike slots = 1 camera)
    Total: 16 cameras (1 entry + 1 exit + 14 indoor)
    """
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_code = Column(String(30), unique=True, nullable=False)  # e.g., "ENTRY_1", "A_CAR_01"
    role = Column(Enum(CameraRole), nullable=False)
    status = Column(Enum(CameraStatus), nullable=False, default=CameraStatus.ACTIVE)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True)  # Null for entry/exit
    rtsp_url = Column(String(255), nullable=False)  # Camera stream URL
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # CV-specific fields
    detection_zones = Column(Text, nullable=True)  # JSON: ROI definitions for slots
    last_detection = Column(DateTime(timezone=True), nullable=True)  # Last vehicle detection
    frames_processed = Column(Integer, default=0)  # Statistics counter
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    floor = relationship("Floor", back_populates="cameras")
    assigned_slots = relationship("Slot", back_populates="camera")
    event_logs = relationship("EventLog", back_populates="camera")
    
    @classmethod
    def generate_camera_code(cls, role: CameraRole, floor_name: str = None, 
                           vehicle_type: str = None, camera_num: int = 1) -> str:
        """Generate camera code following mall convention
        
        Args:
            role: Camera role (ENTRY, EXIT, INDOOR)
            floor_name: "A" or "B" (for indoor cameras)
            vehicle_type: "CAR" or "BIKE" (for indoor cameras)
            camera_num: Sequential number
            
        Returns:
            Camera code like "ENTRY_1", "A_CAR_01", "B_BIKE_01"
        """
        if role in [CameraRole.ENTRY, CameraRole.EXIT]:
            return f"{role.value}_{camera_num}"
        else:  # INDOOR
            return f"{floor_name}_{vehicle_type}_{camera_num:02d}"
