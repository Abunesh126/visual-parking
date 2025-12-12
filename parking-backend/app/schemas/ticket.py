from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TicketBase(BaseModel):
    license_plate: str = Field(..., min_length=1, max_length=20, description="Vehicle license plate", alias="plate_number")
    vehicle_type: str = Field(..., description="Type of vehicle (CAR, BIKE)")

class TicketCreate(TicketBase):
    slot_id: int = Field(..., description="ID of the parking slot")

class TicketUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Ticket status")

class TicketResponse(TicketBase):
    id: int
    slot_id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: str
    
    class Config:
        from_attributes = True
        populate_by_name = True

class TicketCloseRequest(BaseModel):
    exit_time: Optional[datetime] = Field(None, description="Exit time (defaults to now)")

class TicketCloseResponse(TicketResponse):
    parking_duration_minutes: Optional[int] = None