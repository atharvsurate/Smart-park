from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import api_router
from app.api.routes.health import router as health_router
from app.db.session import engine, Base, SessionLocal
from app.services.parking_service import seed_10_initial_slots, sync_dsa_from_db
from app.models.models import ParkingSlot

def init_db_and_dsa():
    """Initializes SQLite tables, seeds 10 initial slots, and synchronizes in-memory DSA structures."""
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        # If no slots exist or previous test set had 20, seed the 10 initial slots
        slot_count = db.query(ParkingSlot).count()
        if slot_count == 0 or slot_count != 10:
            seed_10_initial_slots(db, force=True)
        else:
            sync_dsa_from_db(db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db_and_dsa()
    yield
    # Shutdown
    engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SmartPark Backend API - Smart Parking Queue & Slot Allocation System (Core DSA & SQLite)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix="")

@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_endpoint": f"{settings.API_V1_STR}/health",
        "endpoints": {
            "slots": f"{settings.API_V1_STR}/slots",
            "vehicle_entry": f"{settings.API_V1_STR}/vehicles/entry",
            "vehicle_exit": f"{settings.API_V1_STR}/vehicles/exit",
            "waiting_queue": f"{settings.API_V1_STR}/queue",
            "active_sessions": f"{settings.API_V1_STR}/sessions/active"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
