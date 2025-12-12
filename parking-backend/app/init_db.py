"""Database initialization script for Mall Parking System

Creates the initial database structure with floors, slots, and cameras
based on the mall parking layout specifications.
"""

import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.core.database import engine, get_db
from app.models.floor import Floor
from app.models.slot import Slot, SlotType, SlotStatus
from app.models.camera import Camera, CameraRole, CameraStatus
from app.models.ticket import Ticket
from app.models.event_log import EventLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_floors(db: Session):
    """Create Floor A and B with proper slot counts"""
    floors_data = [
        {'name': 'A', 'total_car_slots': 20, 'total_bike_slots': 16},
        {'name': 'B', 'total_car_slots': 20, 'total_bike_slots': 16}
    ]
    
    floors = []
    for floor_data in floors_data:
        floor = Floor(
            name=floor_data['name'],
            total_car_slots=floor_data['total_car_slots'],
            total_bike_slots=floor_data['total_bike_slots']
        )
        db.add(floor)
        floors.append(floor)
    
    db.flush()  # Get floor IDs
    logger.info(f"Created {len(floors)} floors")
    return floors

def create_slots(db: Session, floors: list):
    """Create parking slots for each floor"""
    slots = []
    
    for floor in floors:
        # Create car slots (20 per floor)
        for slot_num in range(1, 21):
            slot_code = Slot.generate_slot_code(floor.name, SlotType.CAR, slot_num)
            slot = Slot(
                floor_id=floor.id,
                slot_code=slot_code,
                slot_type=SlotType.CAR,
                status=SlotStatus.FREE
            )
            db.add(slot)
            slots.append(slot)
        
        # Create bike slots (16 per floor)
        for slot_num in range(1, 17):
            slot_code = Slot.generate_slot_code(floor.name, SlotType.BIKE, slot_num)
            slot = Slot(
                floor_id=floor.id,
                slot_code=slot_code,
                slot_type=SlotType.BIKE,
                status=SlotStatus.FREE
            )
            db.add(slot)
            slots.append(slot)
    
    db.flush()
    logger.info(f"Created {len(slots)} parking slots")
    return slots

def create_cameras(db: Session, floors: list):
    """Create camera system for mall parking"""
    cameras = []
    
    # Entry camera
    entry_camera = Camera(
        camera_code="ENTRY_1",
        role=CameraRole.ENTRY,
        status=CameraStatus.ACTIVE,
        rtsp_url="rtsp://192.168.1.100:554/entry",
        description="Main entrance gate camera",
        is_active=True
    )
    db.add(entry_camera)
    cameras.append(entry_camera)
    
    # Exit camera
    exit_camera = Camera(
        camera_code="EXIT_1",
        role=CameraRole.EXIT,
        status=CameraStatus.ACTIVE,
        rtsp_url="rtsp://192.168.1.101:554/exit",
        description="Main exit gate camera",
        is_active=True
    )
    db.add(exit_camera)
    cameras.append(exit_camera)
    
    # Indoor cameras for each floor
    camera_ip_base = 102  # Starting IP: 192.168.1.102
    
    for floor in floors:
        # Car cameras (5 per floor - every 4 slots)
        for cam_num in range(1, 6):
            camera_code = Camera.generate_camera_code(
                CameraRole.INDOOR, floor.name, "CAR", cam_num
            )
            camera = Camera(
                camera_code=camera_code,
                role=CameraRole.INDOOR,
                status=CameraStatus.ACTIVE,
                floor_id=floor.id,
                rtsp_url=f"rtsp://192.168.1.{camera_ip_base}:554/car_area",
                description=f"Floor {floor.name} car parking area {cam_num}",
                is_active=True
            )
            db.add(camera)
            cameras.append(camera)
            camera_ip_base += 1
        
        # Bike cameras (2 per floor - every 8 slots)
        for cam_num in range(1, 3):
            camera_code = Camera.generate_camera_code(
                CameraRole.INDOOR, floor.name, "BIKE", cam_num
            )
            camera = Camera(
                camera_code=camera_code,
                role=CameraRole.INDOOR,
                status=CameraStatus.ACTIVE,
                floor_id=floor.id,
                rtsp_url=f"rtsp://192.168.1.{camera_ip_base}:554/bike_area",
                description=f"Floor {floor.name} bike parking area {cam_num}",
                is_active=True
            )
            db.add(camera)
            cameras.append(camera)
            camera_ip_base += 1
    
    db.flush()
    logger.info(f"Created {len(cameras)} cameras")
    return cameras

def initialize_database():
    """Initialize the complete database structure"""
    try:
        # Import all models to ensure tables are created
        from app.core.database import Base
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        try:
            # Check if already initialized
            existing_floors = db.query(Floor).count()
            if existing_floors > 0:
                logger.info("Database already initialized")
                return
            
            logger.info("Initializing database with mall parking structure...")
            
            # Create floors
            floors = create_floors(db)
            
            # Create slots
            slots = create_slots(db, floors)
            
            # Create cameras
            cameras = create_cameras(db, floors)
            
            # Commit all changes
            db.commit()
            
            logger.info("\n" + "="*50)
            logger.info("DATABASE INITIALIZATION COMPLETE")
            logger.info("="*50)
            logger.info(f"Floors created: {len(floors)}")
            logger.info(f"Parking slots: {len(slots)}")
            logger.info(f"Cameras installed: {len(cameras)}")
            logger.info("\nMall Parking Layout:")
            
            for floor in floors:
                car_slots = [s for s in slots if s.floor_id == floor.id and s.slot_type == SlotType.CAR]
                bike_slots = [s for s in slots if s.floor_id == floor.id and s.slot_type == SlotType.BIKE]
                floor_cameras = [c for c in cameras if c.floor_id == floor.id]
                
                logger.info(f"  Floor {floor.name}:")
                logger.info(f"    - Car slots: {len(car_slots)} ({car_slots[0].slot_code} to {car_slots[-1].slot_code})")
                logger.info(f"    - Bike slots: {len(bike_slots)} ({bike_slots[0].slot_code} to {bike_slots[-1].slot_code})")
                logger.info(f"    - Cameras: {len(floor_cameras)}")
            
            logger.info(f"\nGate cameras: Entry ({cameras[0].camera_code}), Exit ({cameras[1].camera_code})")
            logger.info("="*50)
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    initialize_database()