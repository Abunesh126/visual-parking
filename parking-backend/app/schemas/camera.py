from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CameraBase(BaseModel):
    camera_code: str = Field(..., min_length=1, max_length=30, description="Unique camera identifier")
    role: str = Field(..., description="Camera role: ENTRY, EXIT, or INDOOR")
    rtsp_url: str = Field(..., description="Camera RTSP stream URL")
    description: Optional[str] = Field(None, max_length=255, description="Camera description")

class CameraCreate(CameraBase):
    floor_id: Optional[int] = Field(None, description="Floor ID where camera is located")
    status: Optional[str] = Field("ACTIVE", description="Camera status")
    is_active: Optional[bool] = Field(True, description="Whether camera is active")

class CameraUpdate(BaseModel):
    camera_code: Optional[str] = Field(None, min_length=1, max_length=30)
    role: Optional[str] = Field(None, description="Camera role: ENTRY, EXIT, or INDOOR")
    status: Optional[str] = Field(None, description="Camera status")
    rtsp_url: Optional[str] = Field(None, description="Camera RTSP stream URL")
    description: Optional[str] = Field(None, max_length=255)
    floor_id: Optional[int] = Field(None, description="Floor ID")
    is_active: Optional[bool] = Field(None, description="Whether camera is active")

class CameraResponse(CameraBase):
    id: int
    floor_id: Optional[int] = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True