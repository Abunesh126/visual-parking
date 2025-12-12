import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class SlotType(str, enum.Enum):
    """Vehicle type supported in slots"""
    CAR = "CAR"
    BIKE = "BIKE"

class SlotStatus(str, enum.Enum):
    """Parking slot status states"""
    FREE = "FREE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    DISABLED = "DISABLED"

class Slot(Base):
    """Parking slot model with mall-specific layout
    
    Floor A: 20 car slots (A-C-01 to A-C-20), 16 bike slots (A-B-01 to A-B-16)
    Floor B: 20 car slots (B-C-01 to B-C-20), 16 bike slots (B-B-01 to B-B-16)
    """
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=False)
    slot_code = Column(String(20), unique=True, nullable=False)  # e.g., "A-C-01", "B-B-05"
    slot_type = Column(Enum(SlotType), nullable=False)
    status = Column(Enum(SlotStatus), nullable=False, default=SlotStatus.FREE)
    current_plate = Column(String(20), nullable=True)
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)  # Assigned camera
    roi_coordinates = Column(String(100), nullable=True)  # ROI for CV detection (x,y,w,h)
    is_misparked = Column(Boolean, default=False)  # For v2 - misparking detection
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    floor = relationship("Floor", back_populates="slots")
    camera = relationship("Camera", back_populates="assigned_slots")
    tickets = relationship("Ticket", back_populates="slot")
    
    @classmethod
    def generate_slot_code(cls, floor_name: str, slot_type: SlotType, slot_number: int) -> str:
        """Generate slot code following mall convention
        
        Args:
            floor_name: "A" or "B"
            slot_type: SlotType.CAR or SlotType.BIKE  
            slot_number: Sequential number starting from 1
            
        Returns:
            Slot code like "A-C-01" or "B-B-16"
        """
        type_code = "C" if slot_type == SlotType.CAR else "B"
        return f"{floor_name}-{type_code}-{slot_number:02d}"
