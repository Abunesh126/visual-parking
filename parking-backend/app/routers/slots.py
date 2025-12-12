from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.floor import Floor
from app.models.slot import Slot, SlotStatus, SlotType
from app.schemas.slot import SlotResponse, SlotUpdate
from app.schemas.floor import FloorResponse
from typing import List, Optional

router = APIRouter(prefix="/api/v1", tags=["slots"])

@router.get("/slots", response_model=List[SlotResponse])
async def get_slots(
    floor_id: Optional[int] = Query(None, description="Filter by floor ID"),
    status: Optional[str] = Query(None, description="Filter by slot status"),
    slot_type: Optional[str] = Query(None, description="Filter by slot type"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get list of parking slots with optional filters.
    """
    query = db.query(Slot)
    
    if floor_id:
        query = query.filter(Slot.floor_id == floor_id)
    if status:
        query = query.filter(Slot.status == status)
    if slot_type:
        query = query.filter(Slot.slot_type == slot_type)
    
    slots = query.offset(skip).limit(limit).all()
    return slots

@router.get("/slots/{slot_id}", response_model=SlotResponse)
async def get_slot(slot_id: int, db: Session = Depends(get_db)):
    """
    Get specific slot by ID.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with id {slot_id} not found"
        )
    return slot

@router.put("/slots/{slot_id}", response_model=SlotResponse)
async def update_slot(
    slot_id: int,
    slot_update: SlotUpdate,
    db: Session = Depends(get_db)
):
    """
    Update slot information.
    """
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with id {slot_id} not found"
        )
    
    try:
        # Update only provided fields
        if slot_update.status is not None:
            slot.status = SlotStatus(slot_update.status)
        if slot_update.current_plate is not None:
            slot.current_plate = slot_update.current_plate
        
        slot.last_updated = func.now()
        
        db.commit()
        db.refresh(slot)
        return slot
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update slot: {str(e)}"
        )

@router.get("/slots/available", response_model=List[SlotResponse])
async def get_available_slots(
    floor_id: Optional[int] = Query(None, description="Filter by floor ID"),
    slot_type: Optional[str] = Query(None, description="Filter by slot type"),
    db: Session = Depends(get_db)
):
    """
    Get list of available (free) parking slots.
    """
    query = db.query(Slot).filter(Slot.status == SlotStatus.FREE)
    
    if floor_id:
        query = query.filter(Slot.floor_id == floor_id)
    if slot_type:
        query = query.filter(Slot.slot_type == slot_type)
    
    slots = query.all()
    return slots

@router.get("/slots/floor/{floor_id}", response_model=List[SlotResponse])
async def get_slots_by_floor(floor_id: int, db: Session = Depends(get_db)):
    """
    Get all slots on a specific floor.
    """
    # Check if floor exists
    floor = db.query(Floor).filter(Floor.id == floor_id).first()
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Floor with id {floor_id} not found"
        )
    
    slots = db.query(Slot).filter(Slot.floor_id == floor_id).all()
    return slots

@router.get("/slots/search/{slot_code}", response_model=SlotResponse)
async def get_slot_by_code(slot_code: str, db: Session = Depends(get_db)):
    """
    Get slot by its unique code.
    """
    slot = db.query(Slot).filter(Slot.slot_code == slot_code).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot with code {slot_code} not found"
        )
    return slot