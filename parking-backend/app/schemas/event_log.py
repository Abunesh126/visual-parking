from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EventLogBase(BaseModel):
    event_type: str = Field(..., description="Type of event (entry, exit, detection, error)")
    event_category: str = Field(..., description="Category (vehicle, system, camera, payment)")
    event_description: str = Field(..., description="Detailed description of the event")
    severity: Optional[str] = Field("info", description="Severity level (info, warning, error, critical)")

class EventLogCreate(EventLogBase):
    slot_id: Optional[int] = Field(None, description="Related slot ID")
    ticket_id: Optional[int] = Field(None, description="Related ticket ID")
    camera_id: Optional[int] = Field(None, description="Related camera ID")
    floor_id: Optional[int] = Field(None, description="Related floor ID")
    license_plate: Optional[str] = Field(None, max_length=20, description="Vehicle license plate")
    confidence_score: Optional[str] = Field(None, description="AI detection confidence score")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[str] = Field(None, description="Additional metadata as JSON string")

class EventLogResponse(EventLogBase):
    id: int
    slot_id: Optional[int] = None
    ticket_id: Optional[int] = None
    camera_id: Optional[int] = None
    floor_id: Optional[int] = None
    license_plate: Optional[str] = None
    confidence_score: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class EventLogFilter(BaseModel):
    event_type: Optional[str] = Field(None, description="Filter by event type")
    event_category: Optional[str] = Field(None, description="Filter by event category")
    severity: Optional[str] = Field(None, description="Filter by severity level")
    license_plate: Optional[str] = Field(None, description="Filter by license plate")
    slot_id: Optional[int] = Field(None, description="Filter by slot ID")
    camera_id: Optional[int] = Field(None, description="Filter by camera ID")
    start_date: Optional[datetime] = Field(None, description="Filter events from this date")
    end_date: Optional[datetime] = Field(None, description="Filter events until this date")