# Pydantic schemas for API request/response validation
from .ticket import TicketCreate, TicketResponse, TicketUpdate, TicketCloseRequest, TicketCloseResponse
from .slot import (
    SlotCreate, SlotResponse, SlotUpdate, SlotOccupancyRequest, 
    SlotOccupancyResponse, SlotVacateRequest, SlotVacateResponse,
    FloorOccupancyResponse, ParkingOverviewResponse
)
from .floor import FloorCreate, FloorResponse, FloorUpdate, FloorDetailResponse
from .camera import CameraCreate, CameraResponse, CameraUpdate
from .event_log import EventLogCreate, EventLogResponse, EventLogFilter

__all__ = [
    "TicketCreate", "TicketResponse", "TicketUpdate", "TicketCloseRequest", "TicketCloseResponse",
    "SlotCreate", "SlotResponse", "SlotUpdate", "SlotOccupancyRequest", 
    "SlotOccupancyResponse", "SlotVacateRequest", "SlotVacateResponse",
    "FloorOccupancyResponse", "ParkingOverviewResponse",
    "FloorCreate", "FloorResponse", "FloorUpdate", "FloorDetailResponse",
    "CameraCreate", "CameraResponse", "CameraUpdate",
    "EventLogCreate", "EventLogResponse", "EventLogFilter"
]