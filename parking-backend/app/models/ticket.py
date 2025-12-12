import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class VehicleType(str, enum.Enum):
    """Vehicle types supported in mall parking"""
    CAR = "CAR"
    BIKE = "BIKE"

class TicketStatus(str, enum.Enum):
    """Parking ticket status states"""
    ACTIVE = "ACTIVE"      # Vehicle is currently parked
    CLOSED = "CLOSED"      # Vehicle has exited, payment completed
    CANCELLED = "CANCELLED"  # Ticket cancelled/voided

class Ticket(Base):
    """Enhanced parking ticket model for mall system"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20), nullable=False, index=True)
    vehicle_type = Column(Enum(VehicleType), nullable=False)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    
    # Time tracking
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    
    # Status and metadata
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.ACTIVE)
    entry_camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)  # Entry gate camera
    exit_camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)   # Exit gate camera
    
    # CV detection data
    entry_confidence = Column(String(10), nullable=True)  # CV confidence at entry
    entry_image_path = Column(String(255), nullable=True)  # Path to entry snapshot
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    slot = relationship("Slot", back_populates="tickets")
    entry_camera = relationship("Camera", foreign_keys=[entry_camera_id])
    exit_camera = relationship("Camera", foreign_keys=[exit_camera_id])
    event_logs = relationship("EventLog", back_populates="ticket")
    
    @property
    def duration_minutes(self):
        """Calculate parking duration in minutes"""
        if not self.exit_time:
            return 0
        duration = self.exit_time - self.entry_time
        return int(duration.total_seconds() / 60)
    
    @property
    def is_active(self):
        """Check if ticket is currently active"""
        return self.status == TicketStatus.ACTIVE
    
    def __str__(self):
        return f"Ticket {self.id}: {self.plate_number} ({self.vehicle_type}) - {self.status}"
