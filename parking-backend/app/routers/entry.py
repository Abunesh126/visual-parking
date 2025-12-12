from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import get_db
from app.models.event_log import EventLog
from app.models.slot import Slot, SlotStatus, SlotType
from app.models.ticket import Ticket, TicketStatus, VehicleType
from app.models.floor import Floor
from app.schemas.ticket import TicketCreate, TicketResponse
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["entry"])

class SmartSlotAssigner:
    """Intelligent slot assignment based on vehicle type and availability"""
    
    @staticmethod
    def find_optimal_slot(db: Session, vehicle_type: str, 
                         preferred_floor: str = None) -> Optional[Slot]:
        """
        Find the optimal parking slot for a vehicle
        
        Args:
            db: Database session
            vehicle_type: 'CAR' or 'BIKE'
            preferred_floor: Preferred floor name ('A' or 'B')
            
        Returns:
            Optimal slot or None if no slots available
        """
        try:
            # Convert vehicle type to SlotType enum
            slot_type = SlotType.CAR if vehicle_type.upper() == 'CAR' else SlotType.BIKE
            
            # Build base query for available slots
            query = db.query(Slot).filter(
                and_(
                    Slot.slot_type == slot_type,
                    Slot.status == SlotStatus.FREE
                )
            ).join(Floor)
            
            # Apply floor preference if specified
            if preferred_floor:
                query = query.filter(Floor.name == preferred_floor.upper())
            
            # Order by floor and slot code for consistent assignment
            query = query.order_by(Floor.name, Slot.slot_code)
            
            # Get the first available slot
            available_slot = query.first()
            
            if available_slot:
                logger.info(f\"Assigned {slot_type} slot: {available_slot.slot_code}\")\
                return available_slot
            else:\n                # If no slot on preferred floor, try other floors
                if preferred_floor:
                    other_floors_query = db.query(Slot).filter(
                        and_(
                            Slot.slot_type == slot_type,
                            Slot.status == SlotStatus.FREE
                        )
                    ).join(Floor).filter(Floor.name != preferred_floor.upper())
                    
                    alternative_slot = other_floors_query.order_by(Floor.name, Slot.slot_code).first()
                    if alternative_slot:
                        logger.info(f\"Assigned alternative {slot_type} slot: {alternative_slot.slot_code}\")
                        return alternative_slot
                
                logger.warning(f\"No available {slot_type} slots found\")
                return None
                
        except Exception as e:
            logger.error(f\"Slot assignment failed: {e}\")
            return None
    
    @staticmethod
    def get_parking_availability(db: Session) -> dict:
        \"\"\"Get current parking availability statistics\"\"\"
        try:
            # Get total and occupied counts by type and floor
            availability = {}
            
            floors = db.query(Floor).all()
            for floor in floors:
                floor_stats = {
                    'car_slots': {
                        'total': db.query(Slot).filter(
                            and_(Slot.floor_id == floor.id, Slot.slot_type == SlotType.CAR)
                        ).count(),
                        'occupied': db.query(Slot).filter(
                            and_(
                                Slot.floor_id == floor.id,
                                Slot.slot_type == SlotType.CAR, 
                                Slot.status == SlotStatus.OCCUPIED
                            )
                        ).count()
                    },
                    'bike_slots': {
                        'total': db.query(Slot).filter(
                            and_(Slot.floor_id == floor.id, Slot.slot_type == SlotType.BIKE)
                        ).count(),
                        'occupied': db.query(Slot).filter(
                            and_(
                                Slot.floor_id == floor.id,
                                Slot.slot_type == SlotType.BIKE,
                                Slot.status == SlotStatus.OCCUPIED
                            )
                        ).count()
                    }
                }
                
                # Calculate available slots
                floor_stats['car_slots']['available'] = (
                    floor_stats['car_slots']['total'] - floor_stats['car_slots']['occupied']
                )
                floor_stats['bike_slots']['available'] = (
                    floor_stats['bike_slots']['total'] - floor_stats['bike_slots']['occupied']
                )
                
                availability[floor.name] = floor_stats
                
            return availability
            
        except Exception as e:
            logger.error(f\"Failed to get parking availability: {e}\")
            return {}

@router.post(\"/entry-events\", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_entry_event(
    ticket_data: TicketCreate,
    preferred_floor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"
    Create a new entry event with automatic slot assignment
    
    This endpoint simulates the CV system detecting a vehicle at the entry gate:
    1. Vehicle and license plate detection
    2. Vehicle type classification
    3. Intelligent slot assignment
    4. Ticket generation with QR code
    5. Gate control signal
    
    Args:
        ticket_data: Vehicle information from CV detection
        preferred_floor: Optional floor preference ('A' or 'B')
        db: Database session
        
    Returns:
        Parking ticket with assigned slot information
    \"\"\"
    try:
        # Validate vehicle type
        if ticket_data.vehicle_type.upper() not in ['CAR', 'BIKE']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=\"Vehicle type must be 'CAR' or 'BIKE'\"
            )
        
        # Check if vehicle already has an active ticket
        existing_ticket = db.query(Ticket).filter(
            and_(
                Ticket.plate_number == ticket_data.license_plate,
                Ticket.status == TicketStatus.ACTIVE
            )
        ).first()
        
        if existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f\"Vehicle {ticket_data.license_plate} already has active ticket {existing_ticket.id}\"
            )
        
        # Find optimal parking slot using smart assignment
        optimal_slot = SmartSlotAssigner.find_optimal_slot(
            db, ticket_data.vehicle_type, preferred_floor
        )
        
        if not optimal_slot:
            # Check if there are any slots of this type at all
            total_slots = db.query(Slot).filter(
                Slot.slot_type == SlotType.CAR if ticket_data.vehicle_type.upper() == 'CAR' 
                else SlotType.BIKE
            ).count()
            
            if total_slots == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f\"No {ticket_data.vehicle_type} parking slots configured\"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f\"No available {ticket_data.vehicle_type} parking slots. Please try again later.\"
                )
        
        # Create parking ticket
        new_ticket = Ticket(
            plate_number=ticket_data.license_plate,
            vehicle_type=VehicleType(ticket_data.vehicle_type.upper()),
            slot_id=optimal_slot.id,
            entry_time=datetime.utcnow(),
            status=TicketStatus.ACTIVE,
            entry_camera_id=1  # Entry gate camera ID
        )
        db.add(new_ticket)
        
        # Update slot status
        optimal_slot.status = SlotStatus.OCCUPIED
        optimal_slot.current_plate = ticket_data.license_plate
        optimal_slot.last_updated = datetime.utcnow()
        
        # Update floor occupancy counters
        floor = db.query(Floor).filter(Floor.id == optimal_slot.floor_id).first()
        if floor:
            if ticket_data.vehicle_type.upper() == 'CAR':
                floor.occupied_car_slots += 1
            else:
                floor.occupied_bike_slots += 1
        
        # Log entry event for audit trail
        entry_log = EventLog.log_entry_event(
            slot_id=optimal_slot.id,
            license_plate=ticket_data.license_plate,
            vehicle_type=ticket_data.vehicle_type.upper(),
            camera_id=1,  # Entry camera
            confidence=0.95  # High confidence for manual entry
        )
        db.add(entry_log)
        
        # Commit all changes
        db.commit()
        db.refresh(new_ticket)
        
        # Log successful entry
        logger.info(
            f\"Entry processed: {ticket_data.license_plate} ({ticket_data.vehicle_type}) \"
            f\"assigned to slot {optimal_slot.slot_code}\"
        )
        
        return new_ticket
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f\"Entry processing failed: {e}\")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f\"Failed to process entry: {str(e)}\"
        )

@router.get(\"/parking-availability\")
async def get_parking_availability(db: Session = Depends(get_db)):
    \"\"\"
    Get current parking availability across all floors
    
    Returns real-time availability for cars and bikes on each floor
    \"\"\"
    try:
        availability = SmartSlotAssigner.get_parking_availability(db)
        
        # Calculate totals
        total_stats = {
            'total_car_slots': 0,
            'occupied_car_slots': 0,
            'available_car_slots': 0,
            'total_bike_slots': 0,
            'occupied_bike_slots': 0,
            'available_bike_slots': 0
        }
        
        for floor_data in availability.values():
            total_stats['total_car_slots'] += floor_data['car_slots']['total']
            total_stats['occupied_car_slots'] += floor_data['car_slots']['occupied']
            total_stats['available_car_slots'] += floor_data['car_slots']['available']
            
            total_stats['total_bike_slots'] += floor_data['bike_slots']['total']
            total_stats['occupied_bike_slots'] += floor_data['bike_slots']['occupied']
            total_stats['available_bike_slots'] += floor_data['bike_slots']['available']
        
        return {
            'floors': availability,
            'totals': total_stats,
            'timestamp': datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f\"Failed to get availability: {e}\")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=\"Failed to retrieve parking availability\"
        )

@router.post(\"/cv-entry-detection\")
async def handle_cv_entry_detection(
    detection_data: dict,
    db: Session = Depends(get_db)
):
    \"\"\"
    Handle vehicle detection from CV system at entry gate
    
    This endpoint is called by the computer vision system when:
    1. Entry camera detects a vehicle
    2. License plate is successfully recognized
    3. Vehicle type is classified
    
    Args:
        detection_data: CV detection information
        db: Database session
        
    Returns:
        Processing result with slot assignment
    \"\"\"
    try:
        # Extract detection information
        camera_id = detection_data.get('camera_id')
        license_plate = detection_data.get('license_plate')
        vehicle_type = detection_data.get('vehicle_type')
        confidence = detection_data.get('confidence', 0.0)
        
        # Validate detection data
        if not license_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=\"License plate not detected\"
            )
            
        if not vehicle_type or vehicle_type.upper() not in ['CAR', 'BIKE']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=\"Invalid vehicle type detected\"
            )
        
        # Check confidence threshold
        if confidence < 0.7:
            logger.warning(
                f\"Low confidence detection: {license_plate} ({confidence:.2f})\"
            )
            # Could implement manual verification process here
        
        # Create ticket using existing endpoint logic
        ticket_create = TicketCreate(
            license_plate=license_plate,
            vehicle_type=vehicle_type.upper(),
            slot_id=0  # Will be auto-assigned
        )
        
        # Process entry
        ticket_response = await create_entry_event(ticket_create, None, db)
        
        # Log CV detection
        cv_log = EventLog.log_cv_detection(
            camera_id=camera_id,
            license_plate=license_plate,
            vehicle_type=vehicle_type.upper(),
            confidence_score=confidence,
            slot_id=ticket_response.slot_id
        )
        db.add(cv_log)
        db.commit()
        
        return {
            'status': 'success',
            'ticket_id': ticket_response.id,
            'assigned_slot': ticket_response.slot.slot_code,
            'message': f\"Vehicle {license_plate} assigned to slot {ticket_response.slot.slot_code}\",
            'gate_action': 'open'  # Signal to open entry gate
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"CV entry detection failed: {e}\")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f\"CV detection processing failed: {str(e)}\"
        )

@router.get(\"/entry-events\", response_model=List[TicketResponse])
async def get_entry_events(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    vehicle_type: Optional[str] = None,
    floor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"
    Get list of entry events with filtering options
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        active_only: Filter for active tickets only
        vehicle_type: Filter by vehicle type ('CAR' or 'BIKE')
        floor: Filter by floor ('A' or 'B')
        db: Database session
        
    Returns:
        List of ticket records
    \"\"\"
    try:
        query = db.query(Ticket)
        
        # Apply filters
        if active_only:
            query = query.filter(Ticket.status == TicketStatus.ACTIVE)
            
        if vehicle_type:
            query = query.filter(Ticket.vehicle_type == VehicleType(vehicle_type.upper()))
            
        if floor:
            query = query.join(Slot).join(Floor).filter(Floor.name == floor.upper())
        
        # Order by entry time (newest first)
        query = query.order_by(Ticket.entry_time.desc())
        
        tickets = query.offset(skip).limit(limit).all()
        return tickets
        
    except Exception as e:
        logger.error(f\"Failed to get entry events: {e}\")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=\"Failed to retrieve entry events\"
        )

@router.get(\"/entry-events/{ticket_id}\", response_model=TicketResponse)
async def get_entry_event(ticket_id: int, db: Session = Depends(get_db)):
    \"\"\"Get specific entry event by ticket ID\"\"\"
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f\"Ticket with id {ticket_id} not found\"
        )
    return ticket

@router.get(\"/entry-events/license/{license_plate}\", response_model=TicketResponse)
async def get_entry_event_by_license(license_plate: str, db: Session = Depends(get_db)):
    \"\"\"Get active entry event by license plate\"\"\"
    ticket = db.query(Ticket).filter(
        and_(
            Ticket.plate_number == license_plate,
            Ticket.status == TicketStatus.ACTIVE
        )
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f\"No active ticket found for license plate {license_plate}\"
        )
    return ticket