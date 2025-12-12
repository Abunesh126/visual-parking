from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class FloorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=10, description="Floor name/number")

class FloorCreate(FloorBase):
    pass

class FloorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=10, description="Floor name/number")

class FloorResponse(FloorBase):
    id: int
    created_at: datetime
    total_slots: Optional[int] = 0
    occupied_slots: Optional[int] = 0
    available_slots: Optional[int] = 0
    
    class Config:
        from_attributes = True

class FloorDetailResponse(FloorResponse):
    slots: List["SlotResponse"] = []
    cameras: List["CameraResponse"] = []