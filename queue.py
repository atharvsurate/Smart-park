from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import QueueItemResponse
from app.services.parking_service import ParkingService
from app.dsa.queue_manager import waiting_queue_dsa

router = APIRouter(prefix="/queue", tags=["Waiting Queue"])

@router.get("", response_model=List[QueueItemResponse])
def get_waiting_queue(db: Session = Depends(get_db)):
    """
    Returns all vehicles currently waiting in the FIFO queue in order of arrival.
    Time Complexity: O(K) where K is number of waiting vehicles.
    """
    return ParkingService.get_waiting_queue(db)

@router.get("/status")
def get_queue_status():
    """
    Returns high-level statistics about the in-memory queue.
    """
    return {
        "queue_length": waiting_queue_dsa.size(),
        "is_empty": waiting_queue_dsa.is_empty(),
        "front_vehicle": waiting_queue_dsa.peek().license_plate if waiting_queue_dsa.peek() else None,
        "enqueue_complexity": "O(1)",
        "dequeue_complexity": "O(1)"
    }
