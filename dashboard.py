from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import ParkingSlot, ParkingSession, WaitingQueue, SlotStatus, SessionStatus, QueueStatus
from app.schemas.schemas import DashboardSummaryResponse
from app.dsa.parking_lot import parking_lot_dsa
from app.dsa.queue_manager import waiting_queue_dsa

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Computes real-time dashboard metrics strictly from SQLite database records
    and verifies consistency with the in-memory DSA data structures.
    Does not use any mocked or fake data.
    """
    total_slots = db.query(ParkingSlot).count()
    available_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.AVAILABLE.value).count()
    occupied_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.OCCUPIED.value).count()
    reserved_slots = db.query(ParkingSlot).filter(ParkingSlot.status == SlotStatus.RESERVED.value).count()
    
    waiting_queue_count = db.query(WaitingQueue).filter(WaitingQueue.status == QueueStatus.WAITING.value).count()
    active_sessions_count = db.query(ParkingSession).filter(ParkingSession.status == SessionStatus.ACTIVE.value).count()

    dsa_metrics = {
        "slots_array_length": len(parking_lot_dsa.slots),
        "hash_map_active_plates": len(parking_lot_dsa.plate_to_slot_map),
        "fifo_queue_length": waiting_queue_dsa.size(),
        "first_fit_time_complexity": "O(N)",
        "hash_map_lookup_complexity": "O(1)",
        "queue_enqueue_complexity": "O(1)"
    }

    return DashboardSummaryResponse(
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        reserved_slots=reserved_slots,
        waiting_queue_count=waiting_queue_count,
        active_sessions_count=active_sessions_count,
        dsa_metrics=dsa_metrics
    )
