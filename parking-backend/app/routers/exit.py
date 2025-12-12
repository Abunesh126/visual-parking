from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.event_log import EventLog
from app.models.slot import Slot, SlotStatus
from app.models.ticket import Ticket, TicketStatus
from app.schemas.ticket import TicketCloseRequest, TicketCloseResponse
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/v1", tags=["exit"])

@router.post("/exit-events/{ticket_id}", response_model=TicketCloseResponse)
async def create_exit_event(
    ticket_id: int,
    exit_data: TicketCloseRequest = None,
    db: Session = Depends(get_db)
):
    """
    Create an exit event and close the parking ticket.
    """
    # Find the active ticket
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.status == TicketStatus.ACTIVE
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active ticket with id {ticket_id} not found"
        )
    
    # Get the slot
    slot = db.query(Slot).filter(Slot.id == ticket.slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with id {ticket.slot_id} not found"
        )
    
    try:
        # Set exit time
        exit_time = exit_data.exit_time if exit_data and exit_data.exit_time else datetime.utcnow()
        
        # Update ticket
        ticket.exit_time = exit_time
        ticket.status = TicketStatus.CLOSED
        
        # Update slot status
        slot.status = SlotStatus.FREE
        slot.current_plate = None
        slot.last_updated = datetime.utcnow()
        
        # Calculate parking duration
        duration = exit_time - ticket.entry_time
        parking_duration_minutes = int(duration.total_seconds() / 60)
        
        # Log exit event
        exit_log = EventLog.log_exit_event(
            slot_id=slot.id,
            license_plate=ticket.plate_number
        )
        db.add(exit_log)
        
        db.commit()
        db.refresh(ticket)
        
        # Create response
        response = TicketCloseResponse(
            id=ticket.id,
            license_plate=ticket.plate_number,
            vehicle_type=ticket.vehicle_type,
            slot_id=ticket.slot_id,
            entry_time=ticket.entry_time,
            exit_time=ticket.exit_time,
            status=ticket.status,
            parking_duration_minutes=parking_duration_minutes
        )
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exit event: {str(e)}"
        )

@router.post("/exit-events/license/{license_plate}", response_model=TicketCloseResponse)
async def create_exit_event_by_license(
    license_plate: str,
    exit_data: TicketCloseRequest = None,
    db: Session = Depends(get_db)
):
    """
    Create an exit event by license plate number.
    """
    # Find the active ticket by license plate
    ticket = db.query(Ticket).filter(
        Ticket.plate_number == license_plate,
        Ticket.status == TicketStatus.ACTIVE
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active ticket found for license plate {license_plate}"
        )
    
    # Call the main exit event function
    return await create_exit_event(ticket.id, exit_data, db)

@router.get("/exit-events", response_model=List[TicketCloseResponse])
async def get_exit_events(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of completed exit events.
    """
    tickets = db.query(Ticket).filter(
        Ticket.status == TicketStatus.CLOSED
    ).offset(skip).limit(limit).all()
    
    responses = []
    for ticket in tickets:
        duration = None
        if ticket.exit_time and ticket.entry_time:
            duration_delta = ticket.exit_time - ticket.entry_time
            duration = int(duration_delta.total_seconds() / 60)
            
        response = TicketCloseResponse(
            id=ticket.id,
            license_plate=ticket.plate_number,
            vehicle_type=ticket.vehicle_type,
            slot_id=ticket.slot_id,
            entry_time=ticket.entry_time,
            exit_time=ticket.exit_time,
            status=ticket.status,
            parking_duration_minutes=duration
        )
        responses.append(response)
    
    return responses