from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SlotBase(BaseModel):
    slot_number: str
    slot_type: str = "standard"  # standard, compact, ev, accessible
    floor: int = 1

class SlotCreate(SlotBase):
    pass

class SlotResponse(SlotBase):
    id: int
    status: str  # available, occupied, reserved
    current_vehicle_plate: Optional[str] = None
    parked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class VehicleBase(BaseModel):
    license_plate: str
    vehicle_type: str = "car"  # car, suv, bike, ev
    owner_name: Optional[str] = None
    contact_number: Optional[str] = None

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VehicleEntryRequest(BaseModel):
    license_plate: str = Field(..., min_length=2, max_length=20, description="Vehicle license registration number")
    vehicle_type: str = Field("car", description="Vehicle type: car, suv, bike, ev")
    owner_name: Optional[str] = None
    contact_number: Optional[str] = None
    is_priority: bool = Field(False, description="Whether this vehicle has emergency or priority access")

class VehicleEntryResponse(BaseModel):
    status: str  # "allocated" or "queued"
    message: str
    license_plate: str
    vehicle_type: str
    slot_id: Optional[int] = None
    slot_number: Optional[str] = None
    queue_position: Optional[int] = None
    entry_time: datetime

class VehicleExitRequest(BaseModel):
    license_plate: str = Field(..., min_length=2, max_length=20, description="Vehicle license registration number")

class AutoAllocatedVehicleInfo(BaseModel):
    vehicle_id: int
    license_plate: str
    slot_id: int
    slot_number: str
    queue_position_was: int
    allocated_at: datetime

class VehicleExitResponse(BaseModel):
    status: str
    message: str
    license_plate: str
    slot_number: str
    entry_time: datetime
    exit_time: datetime
    duration_minutes: int
    duration_formatted: str
    total_fee: float
    rate_applied: str
    auto_allocated_to_queued_vehicle: Optional[AutoAllocatedVehicleInfo] = None

class QueueItemResponse(BaseModel):
    position: int
    db_queue_id: Optional[int] = None
    vehicle_id: int
    license_plate: str
    vehicle_type: str
    priority_rank: int
    priority_label: str
    entry_time: str

class ActiveSessionResponse(BaseModel):
    session_id: int
    vehicle_id: int
    license_plate: str
    vehicle_type: str
    slot_id: int
    slot_number: str
    floor: int
    entry_time: datetime
    duration_minutes_so_far: int
    estimated_fee_so_far: float

class ReservationRequest(BaseModel):
    license_plate: str = Field(..., min_length=2, max_length=20, description="Vehicle license plate to reserve slot for")
    slot_number: Optional[str] = Field(None, description="Specific slot number to reserve, e.g. S-105. If null, First-Fit slot is allocated.")
    vehicle_type: str = Field("car", description="Vehicle type: car, suv, bike, ev")
    duration_hours: int = Field(1, ge=1, le=24, description="Reservation duration in hours")

class ReservationResponse(BaseModel):
    id: int
    license_plate: str
    slot_id: int
    slot_number: str
    status: str
    reservation_time: datetime
    expires_at: datetime
    message: str

class DashboardSummaryResponse(BaseModel):
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int
    waiting_queue_count: int
    active_sessions_count: int
    dsa_metrics: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str
    environment: str
    database: Dict[str, Any]
    dsa_engine: Dict[str, Any]
    modules: Dict[str, Any]

class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: str = Field(..., min_length=5, max_length=120, description="Email address")
    password: str = Field(..., min_length=6, max_length=100, description="Account password (min 6 chars)")

class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120, description="Registered email address")
    password: str = Field(..., min_length=1, max_length=100, description="Account password")

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
