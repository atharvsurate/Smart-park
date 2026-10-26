from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import ParkingSlot, ParkingSession, SessionStatus, SlotStatus
from app.schemas.schemas import SlotResponse, SlotCreate
from app.services.parking_service import sync_dsa_from_db, seed_10_initial_slots
from app.dsa.parking_lot import parking_lot_dsa

router = APIRouter(prefix="/slots", tags=["Parking Slots"])

@router.get("", response_model=List[SlotResponse])
def get_all_slots(
    status_filter: Optional[str] = None,
    slot_type: Optional[str] = None,
    floor: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all parking slots with current status (Available, Occupied, Reserved).
    Merges database records with active vehicle allocation.
    Time Complexity: O(N) array traversal.
    """
    query = db.query(ParkingSlot)
    if status_filter:
        query = query.filter(ParkingSlot.status == status_filter.lower())
    if slot_type:
        query = query.filter(ParkingSlot.slot_type == slot_type.lower())
    if floor is not None:
        query = query.filter(ParkingSlot.floor == floor)

    db_slots = query.order_by(ParkingSlot.floor, ParkingSlot.slot_number).all()
    
    # Active sessions lookup for vehicle plates
    active_sessions = db.query(ParkingSession).filter(ParkingSession.status == SessionStatus.ACTIVE.value).all()
    session_map = {s.slot_id: (s.vehicle.license_plate if s.vehicle else None, s.entry_time) for s in active_sessions}

    results = []
    for s in db_slots:
        plate, parked_time = session_map.get(s.id, (None, None))
        results.append(SlotResponse(
            id=s.id,
            slot_number=s.slot_number,
            slot_type=s.slot_type,
            status=s.status,
            floor=s.floor,
            current_vehicle_plate=plate,
            parked_at=parked_time,
            created_at=s.created_at
        ))
    return results

@router.get("/available", response_model=List[SlotResponse])
def get_available_slots(
    slot_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Uses DSA First-Fit allocation to return available slots.
    Time Complexity: O(N) linear search.
    """
    sync_dsa_from_db(db)
    query = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.AVAILABLE.value)
    if slot_type:
        query = query.filter(ParkingSlot.slot_type == slot_type.lower())
    slots = query.order_by(ParkingSlot.floor, ParkingSlot.slot_number).all()
    return [
        SlotResponse(
            id=s.id,
            slot_number=s.slot_number,
            slot_type=s.slot_type,
            status=s.status,
            floor=s.floor,
            current_vehicle_plate=None,
            parked_at=None,
            created_at=s.created_at
        )
        for s in slots
    ]

@router.post("", response_model=SlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(slot_in: SlotCreate, db: Session = Depends(get_db)):
    """Add a new parking slot to the system."""
    existing = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_in.slot_number.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slot number '{slot_in.slot_number.upper()}' already exists."
        )

    new_slot = ParkingSlot(
        slot_number=slot_in.slot_number.upper().strip(),
        slot_type=slot_in.slot_type.lower().strip(),
        floor=slot_in.floor,
        status=SlotStatus.AVAILABLE.value
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    sync_dsa_from_db(db)

    return SlotResponse(
        id=new_slot.id,
        slot_number=new_slot.slot_number,
        slot_type=new_slot.slot_type,
        status=new_slot.status,
        floor=new_slot.floor,
        created_at=new_slot.created_at
    )

@router.post("/seed-10", status_code=status.HTTP_200_OK)
def seed_initial_slots_endpoint(force: bool = True, db: Session = Depends(get_db)):
    """
    Seeds exactly 10 initial parking slots (S-101 to S-110).
    When force=True, clears previous demo data for a fresh clean state.
    """
    count = seed_10_initial_slots(db, force=force)
    return {
        "message": f"Successfully initialized {count} parking slots (S-101 to S-110).",
        "slot_count": count
    }
