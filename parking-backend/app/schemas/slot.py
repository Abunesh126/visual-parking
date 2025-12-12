from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class SlotBase(BaseModel):
    slot_code: str = Field(..., min_length=1, max_length=20, description="Unique slot identifier")
    slot_type: str = Field(..., description="Type of slot (CAR, BIKE)")
    floor_id: int = Field(..., description="ID of the floor this slot belongs to")

class SlotCreate(SlotBase):
    pass

class SlotUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Slot status (FREE, OCCUPIED, RESERVED, DISABLED)")
    current_plate: Optional[str] = Field(None, max_length=20, description="License plate of current vehicle")

class SlotResponse(SlotBase):
    id: int
    status: str
    current_plate: Optional[str] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True

class SlotOccupancyRequest(BaseModel):
    license_plate: str = Field(..., min_length=1, max_length=20)
    vehicle_type: str = Field(..., description="Type of vehicle")
    entry_time: Optional[datetime] = Field(None, description="Entry time (defaults to now)")

class SlotOccupancyResponse(BaseModel):
    message: str
    slot: SlotResponse
    ticket_created: bool
    ticket_id: Optional[int] = None

class SlotVacateRequest(BaseModel):
    exit_time: Optional[datetime] = Field(None, description="Exit time (defaults to now)")
    close_ticket: Optional[bool] = Field(True, description="Whether to close associated ticket")

class SlotVacateResponse(BaseModel):
    message: str
    slot: SlotResponse
    ticket_closed: bool
    ticket_id: Optional[int] = None
    parking_duration: Optional[int] = None

class FloorOccupancyResponse(BaseModel):
    floor_id: int
    floor_name: str
    total_slots: int
    occupied_slots: int
    available_slots: int
    occupancy_rate: float

class ParkingOverviewResponse(BaseModel):
    total_floors: int
    total_slots: int
    total_occupied: int
    total_available: int
    overall_occupancy_rate: float
    floors: List[FloorOccupancyResponse]