from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.floor import Floor
from app.models.slot import Slot
from app.models.ticket import Ticket
from app.models.event_log import EventLog
from app.schemas.slot import (
    SlotResponse, SlotOccupancyRequest, SlotOccupancyResponse,
    SlotVacateRequest, SlotVacateResponse, FloorOccupancyResponse,
    ParkingOverviewResponse
)
from datetime import datetime
from typing import List, Optional

router = APIRouter()

@router.get("/slot-occupancy", response_model=ParkingOverviewResponse)
async def get_parking_overview(db: Session = Depends(get_db)):
    """
    Get overall parking occupancy overview including all floors.
    """
    # Get floor occupancy data
    floors_data = db.query(Floor).filter(Floor.is_active == True).all()
    
    total_slots = 0
    total_occupied = 0
    
    floor_responses = []
    for floor in floors_data:
        # Calculate current occupancy
        occupied_count = db.query(Slot).filter(
            Slot.floor_id == floor.id,
            Slot.is_occupied == True
        ).count()
        
        total_count = db.query(Slot).filter(Slot.floor_id == floor.id).count()
        
        # Update floor occupancy if different
        if floor.occupied_slots != occupied_count or floor.total_slots != total_count:
            floor.occupied_slots = occupied_count
            floor.total_slots = total_count
        
        total_slots += total_count
        total_occupied += occupied_count
        
        floor_response = FloorOccupancyResponse(
            floor_id=floor.id,
            floor_number=floor.floor_number,
            floor_name=floor.floor_name,
            total_slots=total_count,
            occupied_slots=occupied_count,
            available_slots=total_count - occupied_count,
            occupancy_rate=floor.occupancy_rate,
            is_active=floor.is_active
        )
        floor_responses.append(floor_response)
    
    db.commit()
    
    overall_occupancy_rate = (total_occupied / total_slots * 100) if total_slots > 0 else 0
    
    return ParkingOverviewResponse(
        total_floors=len(floors_data),
        total_slots=total_slots,
        total_occupied=total_occupied,
        total_available=total_slots - total_occupied,
        overall_occupancy_rate=round(overall_occupancy_rate, 2),
        floors=floor_responses
    )

@router.get("/slot-occupancy/floor/{floor_id}", response_model=List[SlotResponse])
async def get_floor_slots(
    floor_id: int,
    occupied_only: Optional[bool] = Query(None, description="Filter by occupancy status"),
    db: Session = Depends(get_db)
):
    """
    Get all slots for a specific floor with their occupancy status.
    """
    # Verify floor exists
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Floor with id {floor_id} not found"
        )
    
    query = db.query(Slot).filter(Slot.floor_id == floor_id)
    
    if occupied_only is not None:
        query = query.filter(Slot.is_occupied == occupied_only)
    
    slots = query.all()
    return slots

@router.post("/slot-occupancy/{slot_id}/occupy", response_model=SlotOccupancyResponse)
async def occupy_slot(
    slot_id: int,
    occupancy_data: SlotOccupancyRequest,
    create_ticket: bool = Query(True, description="Whether to create a parking ticket"),
    db: Session = Depends(get_db)
):
    """
    Mark a slot as occupied by a vehicle.
    Optionally create a parking ticket for billing.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with id {slot_id} not found"
        )
    
    if slot.is_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slot {slot.slot_number} is already occupied"
        )
    
    try:
        entry_time = occupancy_data.entry_time or datetime.utcnow()
        
        # Update slot
        slot.is_occupied = True
        slot.license_plate = occupancy_data.license_plate
        slot.vehicle_type = occupancy_data.vehicle_type
        slot.entry_time = entry_time
        slot.status = "occupied"
        slot.camera_detection = occupancy_data.camera_detection
        
        # Update floor occupancy
        if slot.floor:
            slot.floor.occupied_slots += 1
        
        ticket_created = False
        ticket_id = None
        
        # Create ticket if requested
        if create_ticket:
            # Check for existing active ticket
            existing_ticket = db.query(Ticket).filter(
                Ticket.license_plate == occupancy_data.license_plate,
                Ticket.is_active == True
            ).first()
            
            if not existing_ticket:
                new_ticket = Ticket(
                    slot_id=slot_id,
                    license_plate=occupancy_data.license_plate,
                    vehicle_type=occupancy_data.vehicle_type,
                    entry_time=entry_time
                )
                db.add(new_ticket)
                ticket_created = True
                db.flush()
                ticket_id = new_ticket.id
        
        # Log occupancy event
        occupancy_log = EventLog.log_entry_event(
            slot_id=slot.id,
            license_plate=occupancy_data.license_plate
        )
        db.add(occupancy_log)
        
        db.commit()
        db.refresh(slot)
        
        return SlotOccupancyResponse(
            message=f"Slot {slot.slot_number} successfully occupied",
            slot=slot,
            ticket_created=ticket_created,
            ticket_id=ticket_id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to occupy slot: {str(e)}"
        )

@router.post("/slot-occupancy/{slot_id}/vacate", response_model=SlotVacateResponse)
async def vacate_slot(
    slot_id: int,
    vacate_data: SlotVacateRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a slot as vacant (vehicle left).
    Optionally close the associated parking ticket.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with id {slot_id} not found"
        )
    
    if not slot.is_occupied:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slot {slot.slot_number} is not occupied"
        )
    
    try:
        exit_time = vacate_data.exit_time or datetime.utcnow()
        license_plate = slot.license_plate
        
        ticket_closed = False
        ticket_id = None
        parking_duration = None
        total_amount = None
        
        # Handle ticket closure if requested
        if vacate_data.close_ticket:
            active_ticket = db.query(Ticket).filter(
                Ticket.slot_id == slot_id,
                Ticket.is_active == True
            ).first()
            
            if active_ticket:
                active_ticket.close_ticket(exit_time)
                ticket_closed = True
                ticket_id = active_ticket.id
                parking_duration = active_ticket.duration_minutes
                total_amount = active_ticket.total_amount
        
        # Update slot
        slot.is_occupied = False
        slot.exit_time = exit_time
        slot.status = "available"
        
        # Clear slot data
        previous_license = slot.license_plate
        slot.license_plate = None
        slot.vehicle_type = None
        slot.camera_detection = False
        
        # Update floor occupancy
        if slot.floor and slot.floor.occupied_slots > 0:
            slot.floor.occupied_slots -= 1
        
        # Log exit event
        exit_log = EventLog.log_exit_event(
            slot_id=slot.id,
            license_plate=previous_license
        )
        db.add(exit_log)
        
        db.commit()
        db.refresh(slot)
        
        return SlotVacateResponse(
            message=f"Slot {slot.slot_number} successfully vacated",
            slot=slot,
            ticket_closed=ticket_closed,
            ticket_id=ticket_id,
            parking_duration=parking_duration,
            total_amount=total_amount
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to vacate slot: {str(e)}"
        )

@router.get("/slot-occupancy/slot/{slot_number}", response_model=SlotResponse)
async def get_slot_by_number(
    slot_number: str,
    floor_number: Optional[int] = Query(None, description="Floor number to narrow search"),
    db: Session = Depends(get_db)
):
    """
    Get slot information by slot number.
    """
    query = db.query(Slot).filter(Slot.slot_number == slot_number)
    
    if floor_number is not None:
        query = query.join(Floor).filter(Floor.floor_number == floor_number)
    
    slot = query.first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot {slot_number} not found"
        )
    
    return slot