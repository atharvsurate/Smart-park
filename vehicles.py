from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import (
    VehicleEntryRequest,
    VehicleEntryResponse,
    VehicleExitRequest,
    VehicleExitResponse
)
from app.services.parking_service import ParkingService
from app.models.models import Vehicle, ParkingSession, SessionStatus
from app.dsa.parking_lot import parking_lot_dsa

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.post("/entry", response_model=VehicleEntryResponse, status_code=status.HTTP_201_CREATED)
def register_entry(payload: VehicleEntryRequest, db: Session = Depends(get_db)):
    """
    Register vehicle arrival:
    - Verifies no active duplicate session exists.
    - Allocates the first available slot automatically via First-Fit DSA search.
    - If all slots are full, adds vehicle to FIFO waiting queue.
    """
    return ParkingService.register_vehicle_entry(payload, db)

@router.post("/exit", response_model=VehicleExitResponse)
def process_exit(payload: VehicleExitRequest, db: Session = Depends(get_db)):
    """
    Process vehicle departure:
    - Locates vehicle active parking session via Hash Map / DB.
    - Computes duration and parking charges.
    - Releases slot to Available.
    - If a vehicle is waiting in FIFO queue, immediately allocates slot to it.
    """
    return ParkingService.process_vehicle_exit(payload, db)

@router.get("/search/{license_plate}")
def search_vehicle(license_plate: str, db: Session = Depends(get_db)):
    """
    Quick search for a vehicle by registration number using O(1) Hash Map
    and SQLite records.
    """
    plate = license_plate.strip().upper()
    
    # Check in-memory Hash Map (O(1))
    slot_node = parking_lot_dsa.find_vehicle_slot(plate)

    vehicle = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No vehicle found with license plate '{plate}'."
        )

    active_session = db.query(ParkingSession).filter(
        ParkingSession.vehicle_id == vehicle.id,
        ParkingSession.status == SessionStatus.ACTIVE.value
    ).first()

    return {
        "license_plate": vehicle.license_plate,
        "vehicle_type": vehicle.vehicle_type,
        "owner_name": vehicle.owner_name,
        "is_currently_parked": active_session is not None,
        "current_slot": slot_node.slot_number if slot_node else (active_session.slot.slot_number if active_session else None),
        "entry_time": active_session.entry_time.isoformat() if active_session else None
    }
