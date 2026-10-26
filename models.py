from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"

class SlotType(str, enum.Enum):
    STANDARD = "standard"
    COMPACT = "compact"
    EV = "ev"
    ACCESSIBLE = "accessible"

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"

class ReservationStatus(str, enum.Enum):
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class QueueStatus(str, enum.Enum):
    WAITING = "waiting"
    ALLOCATED = "allocated"
    CANCELLED = "cancelled"

class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String(20), unique=True, index=True, nullable=False)
    slot_type = Column(String(20), default=SlotType.STANDARD.value, nullable=False)
    status = Column(String(20), default=SlotStatus.AVAILABLE.value, nullable=False)
    floor = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = relationship("ParkingSession", back_populates="slot")
    reservations = relationship("Reservation", back_populates="slot")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(30), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(20), default="car", nullable=False)
    owner_name = Column(String(100), nullable=True)
    contact_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    sessions = relationship("ParkingSession", back_populates="vehicle")
    reservations = relationship("Reservation", back_populates="vehicle")
    queue_entries = relationship("WaitingQueue", back_populates="vehicle")

class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    exit_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    total_fee = Column(Float, nullable=True)
    status = Column(String(20), default=SessionStatus.ACTIVE.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    vehicle = relationship("Vehicle", back_populates="sessions")
    slot = relationship("ParkingSlot", back_populates="sessions")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    reservation_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default=ReservationStatus.ACTIVE.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    vehicle = relationship("Vehicle", back_populates="reservations")
    slot = relationship("ParkingSlot", back_populates="reservations")

class WaitingQueue(Base):
    __tablename__ = "waiting_queue"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 0: standard, 1: priority/emergency
    entry_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(20), default=QueueStatus.WAITING.value, nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="queue_entries")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
