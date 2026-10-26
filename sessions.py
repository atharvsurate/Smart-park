from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import ActiveSessionResponse
from app.services.parking_service import ParkingService
from app.models.models import ParkingSession, SessionStatus

router = APIRouter(prefix="/sessions", tags=["Parking Sessions"])

@router.get("/active", response_model=List[ActiveSessionResponse])
def get_active_sessions(db: Session = Depends(get_db)):
    """
    Returns all active parking sessions with real-time calculated duration
    and estimated parking charges.
    """
    return ParkingService.get_active_sessions(db)

@router.get("/history")
def get_completed_sessions(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns past completed parking sessions with departure time and charges collected.
    """
    sessions = db.query(ParkingSession).filter(
        ParkingSession.status == SessionStatus.COMPLETED.value
    ).order_by(ParkingSession.exit_time.desc()).limit(limit).all()

    return [
        {
            "session_id": s.id,
            "license_plate": s.vehicle.license_plate if s.vehicle else "UNKNOWN",
            "vehicle_type": s.vehicle.vehicle_type if s.vehicle else "car",
            "slot_number": s.slot.slot_number if s.slot else f"#{s.slot_id}",
            "floor": s.slot.floor if s.slot else 1,
            "entry_time": s.entry_time.isoformat(),
            "exit_time": s.exit_time.isoformat() if s.exit_time else None,
            "duration_minutes": s.duration_minutes,
            "total_fee": s.total_fee
        }
        for s in sessions
    ]
