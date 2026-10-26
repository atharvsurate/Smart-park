from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import ReservationRequest, ReservationResponse
from app.services.parking_service import ParkingService

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationRequest, db: Session = Depends(get_db)):
    """
    Reserve a parking slot:
    - Sets slot status to RESERVED.
    - Prevents double allocation (slot cannot be allocated to regular traffic).
    """
    return ParkingService.create_reservation(payload, db)

@router.get("", response_model=List[ReservationResponse])
def get_reservations(db: Session = Depends(get_db)):
    """Retrieve all active slot reservations."""
    return ParkingService.get_active_reservations(db)

@router.post("/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Cancel reservation and release the reserved slot back to available."""
    return ParkingService.cancel_reservation(reservation_id, db)
