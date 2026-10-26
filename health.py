from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.db.session import check_db_connection
from app.dsa.parking_lot import parking_lot_dsa
from app.dsa.queue_manager import waiting_queue_dsa

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    """
    Health check endpoint returning the real runtime status of the SmartPark backend,
    including SQLite database connectivity and DSA in-memory structures.
    """
    db_status = check_db_connection()
    is_healthy = db_status.get("status") == "connected"

    dsa_status = {
        "status": "ready",
        "structures": {
            "slots_array": {"type": "Array/List", "length": len(parking_lot_dsa.slots)},
            "vehicle_lookup_map": {"type": "Hash Map", "entries": len(parking_lot_dsa.plate_to_slot_map)},
            "waiting_queue": {"type": "FIFO Queue & Priority Heap", "length": waiting_queue_dsa.size()}
        }
    }

    return {
        "status": "healthy" if is_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "dsa_engine": dsa_status,
        "modules": {
            "dashboard": {"status": "ready", "description": "System overview & real-time slot telemetry"},
            "parking_slots": {"status": "ready", "description": "Array-based slot allocation & visualization"},
            "vehicles": {"status": "ready", "description": "Vehicle registry and fast hash map lookups"},
            "queue_management": {"status": "ready", "description": "FIFO queue & Priority queue dispatching"},
            "reservations": {"status": "ready", "description": "Pre-booking slot reservation system"},
            "parking_history": {"status": "ready", "description": "Parking sessions, duration & tariff computation"},
            "analytics": {"status": "ready", "description": "Data-driven parking utilization & revenue metrics"}
        }
    }
