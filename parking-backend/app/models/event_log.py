from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship\nfrom app.core.database import Base
from datetime import datetime

class EventLog(Base):
    """Enhanced event logging for mall parking system with CV integration"""
    __tablename__ = \"event_logs\"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # entry, exit, detection, slot_change
    event_category = Column(String(50), nullable=False)  # vehicle, system, camera, cv_detection
    event_description = Column(Text, nullable=False)
    
    # Foreign key relationships
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)  
    camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    floor_id = Column(Integer, ForeignKey("floors.id"), nullable=True)
    
    # Vehicle and detection data
    license_plate = Column(String(20), nullable=True)
    vehicle_type = Column(String(10), nullable=True)  # CAR, BIKE
    confidence_score = Column(String(10), nullable=True)  # CV detection confidence
    
    # Technical fields
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True) 
    session_id = Column(String(100), nullable=True)
    severity = Column(String(20), default="info")  # info, warning, error, critical
    metadata = Column(Text, nullable=True)  # JSON string for additional CV data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    slot = relationship("Slot", back_populates="event_logs", lazy="select")
    ticket = relationship("Ticket", back_populates="event_logs", lazy="select")  
    camera = relationship("Camera", back_populates="event_logs", lazy="select")
    
    @classmethod
    def log_entry_event(cls, slot_id, license_plate, vehicle_type, camera_id=None, confidence=None):
        """Log vehicle entry event detected by CV"""
        return cls(
            event_type="entry",
            event_category="vehicle",
            event_description=f"{vehicle_type} {license_plate} entered slot {slot_id}",
            slot_id=slot_id,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            camera_id=camera_id,
            confidence_score=str(confidence) if confidence else None,
            severity="info"
        )
    
    @classmethod
    def log_exit_event(cls, slot_id, license_plate, vehicle_type, camera_id=None):
        """Log vehicle exit event detected by CV"""
        return cls(
            event_type="exit", 
            event_category="vehicle",
            event_description=f"{vehicle_type} {license_plate} exited from slot {slot_id}",
            slot_id=slot_id,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            camera_id=camera_id,
            severity="info"
        )
    
    @classmethod
    def log_cv_detection(cls, camera_id, license_plate, vehicle_type, confidence_score, slot_id=None):
        """Log computer vision detection event"""
        return cls(
            event_type="detection",
            event_category="cv_detection", 
            event_description=f"CV detected {vehicle_type} {license_plate} (conf: {confidence_score})",
            camera_id=camera_id,
            slot_id=slot_id,
            license_plate=license_plate,
            vehicle_type=vehicle_type,
            confidence_score=str(confidence_score),
            severity="info"
        )
    
    @classmethod
    def log_slot_occupancy_change(cls, slot_id, old_status, new_status, plate=None, camera_id=None):
        """Log slot occupancy changes detected by indoor cameras"""
        return cls(
            event_type="slot_change",
            event_category="camera",
            event_description=f"Slot {slot_id} status: {old_status} → {new_status}",
            slot_id=slot_id,
            camera_id=camera_id,
            license_plate=plate,
            severity="info"
        )
    
    @classmethod
    def log_system_error(cls, error_description, camera_id=None, metadata=None):
        """Log system errors in CV processing"""
        return cls(
            event_type="error",
            event_category="system", 
            event_description=error_description,
            camera_id=camera_id,
            metadata=metadata,
            severity="error"
        )