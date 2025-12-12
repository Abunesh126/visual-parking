from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Floor(Base):
    """Floor model representing parking floors (A, B)"""
    __tablename__ = "floors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(10), unique=True, nullable=False)  # "A" or "B"
    total_car_slots = Column(Integer, default=20)  # 20 car slots per floor
    total_bike_slots = Column(Integer, default=16)  # 16 bike slots per floor
    occupied_car_slots = Column(Integer, default=0)
    occupied_bike_slots = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    slots = relationship("Slot", back_populates="floor")
    cameras = relationship("Camera", back_populates="floor")
    
    @property
    def total_slots(self):
        """Calculate total slots on this floor"""
        return self.total_car_slots + self.total_bike_slots
    
    @property
    def total_occupied(self):
        """Calculate total occupied slots"""
        return self.occupied_car_slots + self.occupied_bike_slots
    
    @property
    def occupancy_rate(self):
        """Calculate occupancy percentage"""
        if self.total_slots == 0:
            return 0.0
        return (self.total_occupied / self.total_slots) * 100
