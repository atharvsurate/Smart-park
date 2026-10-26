"""
SmartPark Core Parking Service
==============================
Business logic coordinating:
1. ParkingLotDSA (Array/List & Hash Map)
2. WaitingQueueDSA (FIFO Queue & Priority Min-Heap)
3. SQLite Persistence (SQLAlchemy models)
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    ParkingSlot,
    Vehicle,
    ParkingSession,
    WaitingQueue,
    Reservation,
    SlotStatus,
    SessionStatus,
    QueueStatus,
    ReservationStatus,
    SlotType
)
from app.dsa.parking_lot import parking_lot_dsa, SlotNode
from app.dsa.queue_manager import waiting_queue_dsa, QueuedVehicle
from app.schemas.schemas import (
    VehicleEntryRequest,
    VehicleEntryResponse,
    VehicleExitRequest,
    VehicleExitResponse,
    AutoAllocatedVehicleInfo,
    ActiveSessionResponse,
    QueueItemResponse,
    ReservationRequest,
    ReservationResponse,
    SlotResponse
)

def sync_dsa_from_db(db: Session) -> None:
    """
    Synchronizes in-memory DSA data structures (Array + Hash Map + FIFO Queue)
    with the current state in the SQLite database.
    Time Complexity: O(N + S + K) where N = slots, S = active sessions, K = waiting queue size.
    """
    slots = db.query(ParkingSlot).order_by(ParkingSlot.floor, ParkingSlot.slot_number).all()
    active_sessions = db.query(ParkingSession).filter(ParkingSession.status == SessionStatus.ACTIVE.value).all()
    parking_lot_dsa.load_from_db_records(slots, active_sessions)

    waiting_items = db.query(WaitingQueue).filter(WaitingQueue.status == QueueStatus.WAITING.value).all()
    waiting_queue_dsa.load_from_db_records(waiting_items)

def seed_10_initial_slots(db: Session, force: bool = False) -> int:
    """
    Seeds exactly 10 initial parking slots with unique IDs (S-101 through S-110).
    Categorized into Standard, Compact, EV Charging, and Accessible.
    """
    existing_count = db.query(ParkingSlot).count()
    if existing_count > 0 and not force:
        return existing_count

    if force:
        # Clear existing sessions, queue, reservations, and slots
        db.query(ParkingSession).delete()
        db.query(WaitingQueue).delete()
        db.query(ParkingSlot).delete()
        db.commit()

    initial_slots_spec = [
        {"slot_number": "S-101", "slot_type": "standard", "floor": 1},
        {"slot_number": "S-102", "slot_type": "standard", "floor": 1},
        {"slot_number": "S-103", "slot_type": "standard", "floor": 1},
        {"slot_number": "S-104", "slot_type": "compact", "floor": 1},
        {"slot_number": "S-105", "slot_type": "compact", "floor": 1},
        {"slot_number": "S-106", "slot_type": "ev", "floor": 1},
        {"slot_number": "S-107", "slot_type": "ev", "floor": 1},
        {"slot_number": "S-108", "slot_type": "accessible", "floor": 1},
        {"slot_number": "S-109", "slot_type": "standard", "floor": 2},
        {"slot_number": "S-110", "slot_type": "standard", "floor": 2},
    ]

    for spec in initial_slots_spec:
        slot = ParkingSlot(
            slot_number=spec["slot_number"],
            slot_type=spec["slot_type"],
            floor=spec["floor"],
            status=SlotStatus.AVAILABLE.value
        )
        db.add(slot)

    db.commit()
    sync_dsa_from_db(db)
    return len(initial_slots_spec)

def format_duration(minutes: int) -> str:
    """Returns human-readable duration, e.g. '1 hr 15 mins' or '25 mins'."""
    hours = minutes // 60
    rem_mins = minutes % 60
    if hours > 0:
        return f"{hours} hr {rem_mins} mins" if rem_mins > 0 else f"{hours} hr"
    return f"{rem_mins} mins"

def calculate_parking_charges(entry_time: datetime, exit_time: datetime) -> tuple[int, float, str]:
    """
    Computes parking duration and tariff using configurable hourly rate and grace period.
    Formula:
      - If duration <= GRACE_PERIOD_MINUTES (default 15m): Free (₹0.0)
      - Else: ceil(duration_minutes / 60) * BASE_HOURLY_RATE (default ₹20/hr)
    """
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    if exit_time.tzinfo is None:
        exit_time = exit_time.replace(tzinfo=timezone.utc)

    duration_seconds = max(0.0, (exit_time - entry_time).total_seconds())
    duration_minutes = max(1, int(duration_seconds // 60))

    if duration_minutes <= settings.GRACE_PERIOD_MINUTES:
        fee = 0.0
        rate_applied = f"Grace period applied (<= {settings.GRACE_PERIOD_MINUTES} mins: Free)"
    else:
        billable_hours = math.ceil(duration_minutes / 60.0)
        fee = round(billable_hours * settings.BASE_HOURLY_RATE, 2)
        rate_applied = f"₹{settings.BASE_HOURLY_RATE}/hr ({settings.GRACE_PERIOD_MINUTES} min grace period)"

    return duration_minutes, fee, rate_applied

class ParkingService:
    @staticmethod
    def register_vehicle_entry(payload: VehicleEntryRequest, db: Session) -> VehicleEntryResponse:
        """
        Vehicle Entry Workflow:
        1. Validates and normalizes registration plate.
        2. Checks if vehicle has an active parking session (via Hash Map & DB).
        3. Checks if vehicle is already in the waiting queue.
        4. Searches for first available slot via First-Fit DSA search.
        5. If available: Allocates slot, updates DB + Hash Map, creates active session.
        6. If full: Enqueues vehicle into FIFO waiting queue.
        """
        plate = payload.license_plate.strip().upper()
        now = datetime.now(timezone.utc)

        # Step 2: Prevent duplicate active parking sessions
        active_slot = parking_lot_dsa.find_vehicle_slot(plate)
        if active_slot:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{plate}' already has an active parking session in slot '{active_slot.slot_number}'."
            )

        db_active_session = db.query(ParkingSession).join(Vehicle).filter(
            Vehicle.license_plate == plate,
            ParkingSession.status == SessionStatus.ACTIVE.value
        ).first()
        if db_active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{plate}' already has an active parking session in slot '{db_active_session.slot.slot_number}'."
            )

        # Step 3: Prevent duplicate queue entry
        existing_queue = db.query(WaitingQueue).join(Vehicle).filter(
            Vehicle.license_plate == plate,
            WaitingQueue.status == QueueStatus.WAITING.value
        ).first()
        if existing_queue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{plate}' is already waiting in the queue."
            )

        # Step 4: Fetch or create vehicle record in SQLite
        vehicle = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
        if not vehicle:
            vehicle = Vehicle(
                license_plate=plate,
                vehicle_type=payload.vehicle_type.lower().strip(),
                owner_name=payload.owner_name.strip() if payload.owner_name else None,
                contact_number=payload.contact_number.strip() if payload.contact_number else None
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)
        else:
            vehicle.vehicle_type = payload.vehicle_type.lower().strip()
            if payload.owner_name:
                vehicle.owner_name = payload.owner_name.strip()
            if payload.contact_number:
                vehicle.contact_number = payload.contact_number.strip()
            db.commit()

        # Step 4b: Check if vehicle has an active reservation for a held slot
        active_res = db.query(Reservation).filter(
            Reservation.vehicle_id == vehicle.id,
            Reservation.status == ReservationStatus.ACTIVE.value
        ).first()

        if active_res:
            res_slot = active_res.slot
            if res_slot and res_slot.status == SlotStatus.RESERVED.value:
                # Fulfill reservation and transition slot to occupied
                res_slot.status = SlotStatus.OCCUPIED.value
                active_res.status = ReservationStatus.FULFILLED.value

                session = ParkingSession(
                    vehicle_id=vehicle.id,
                    slot_id=res_slot.id,
                    entry_time=now,
                    status=SessionStatus.ACTIVE.value
                )
                db.add(session)
                db.commit()
                db.refresh(session)

                parking_lot_dsa.allocate_slot(res_slot.id, plate)

                return VehicleEntryResponse(
                    status="allocated",
                    message=f"Vehicle '{plate}' successfully checked into its reserved slot '{res_slot.slot_number}'.",
                    license_plate=plate,
                    vehicle_type=vehicle.vehicle_type,
                    slot_id=res_slot.id,
                    slot_number=res_slot.slot_number,
                    queue_position=None,
                    entry_time=now
                )

        # Step 5: Check slot availability using First-Fit algorithm (only searches 'available' slots)
        # Try preferred slot type if specified, or first available
        target_type = payload.vehicle_type.lower().strip()
        preferred_slot_type = "ev" if target_type == "ev" else ("compact" if target_type == "bike" else None)
        
        available_node = parking_lot_dsa.find_available_slot(slot_type=preferred_slot_type)
        if not available_node:
            # Fallback to any available slot
            available_node = parking_lot_dsa.find_available_slot(slot_type=None)

        if available_node:
            # Atomic update in SQLite
            db_slot = db.query(ParkingSlot).filter(
                ParkingSlot.id == available_node.id,
                ParkingSlot.status == SlotStatus.AVAILABLE.value
            ).first()

            if not db_slot:
                # Concurrent conflict guard: re-sync and retry
                sync_dsa_from_db(db)
                available_node = parking_lot_dsa.find_available_slot()

            if db_slot and db_slot.status == SlotStatus.AVAILABLE.value:
                db_slot.status = SlotStatus.OCCUPIED.value

                # Create active parking session
                session = ParkingSession(
                    vehicle_id=vehicle.id,
                    slot_id=db_slot.id,
                    entry_time=now,
                    status=SessionStatus.ACTIVE.value
                )
                db.add(session)
                db.commit()
                db.refresh(session)

                # Update in-memory DSA Array & Hash Map (O(1) insertion)
                parking_lot_dsa.allocate_slot(db_slot.id, plate)

                return VehicleEntryResponse(
                    status="allocated",
                    message=f"Vehicle '{plate}' successfully allocated to slot '{db_slot.slot_number}'.",
                    license_plate=plate,
                    vehicle_type=vehicle.vehicle_type,
                    slot_id=db_slot.id,
                    slot_number=db_slot.slot_number,
                    queue_position=None,
                    entry_time=now
                )

        # Step 6: All slots full -> Add to FIFO Waiting Queue
        queue_record = WaitingQueue(
            vehicle_id=vehicle.id,
            priority=1 if payload.is_priority else 0,
            entry_time=now,
            status=QueueStatus.WAITING.value
        )
        db.add(queue_record)
        db.commit()
        db.refresh(queue_record)

        # Update in-memory waiting queue DSA
        if payload.is_priority:
            waiting_queue_dsa.enqueue_priority(
                vehicle_id=vehicle.id,
                license_plate=plate,
                vehicle_type=vehicle.vehicle_type,
                priority_level=0,
                db_queue_id=queue_record.id
            )
        else:
            waiting_queue_dsa.enqueue_fifo(
                vehicle_id=vehicle.id,
                license_plate=plate,
                vehicle_type=vehicle.vehicle_type,
                db_queue_id=queue_record.id
            )

        position = waiting_queue_dsa.size()

        return VehicleEntryResponse(
            status="queued",
            message=f"All slots are occupied. Vehicle '{plate}' added to FIFO waiting queue at position {position}.",
            license_plate=plate,
            vehicle_type=vehicle.vehicle_type,
            slot_id=None,
            slot_number=None,
            queue_position=position,
            entry_time=now
        )

    @staticmethod
    def process_vehicle_exit(payload: VehicleExitRequest, db: Session) -> VehicleExitResponse:
        """
        Vehicle Exit Workflow:
        1. Locates active session using Hash Map O(1) or SQLite query.
        2. Calculates elapsed duration and parking fees.
        3. Marks session as COMPLETED with fees and exit time.
        4. Releases slot to AVAILABLE in both SQLite and in-memory Array.
        5. Automatic Queue Dispatch: If vehicles are waiting in FIFO queue,
           immediately allocates the newly released slot to the head of the queue.
        """
        plate = payload.license_plate.strip().upper()
        now = datetime.now(timezone.utc)

        # Find active session in SQLite
        session = db.query(ParkingSession).join(Vehicle).filter(
            Vehicle.license_plate == plate,
            ParkingSession.status == SessionStatus.ACTIVE.value
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active parking session found for vehicle '{plate}'."
            )

        slot = session.slot
        slot_number = slot.slot_number
        slot_id = slot.id

        # Calculate duration and tariff charges
        duration_minutes, fee, rate_applied = calculate_parking_charges(session.entry_time, now)

        # Complete session
        session.exit_time = now
        session.duration_minutes = duration_minutes
        session.total_fee = fee
        session.status = SessionStatus.COMPLETED.value

        # Release slot
        slot.status = SlotStatus.AVAILABLE.value
        parking_lot_dsa.release_slot(slot_id)

        # Step 5: Check FIFO Waiting Queue for automatic slot allocation
        auto_allocated_info = None

        # Look for next waiting vehicle in SQLite (ordered by priority desc, entry_time asc)
        next_waiting_entry = db.query(WaitingQueue).filter(
            WaitingQueue.status == QueueStatus.WAITING.value
        ).order_by(WaitingQueue.priority.desc(), WaitingQueue.entry_time.asc()).first()

        if next_waiting_entry:
            # Dequeue from in-memory FIFO queue
            dequeued_item = waiting_queue_dsa.dequeue()

            # Mark queue record as allocated in SQLite
            next_waiting_entry.status = QueueStatus.ALLOCATED.value

            # Allocate released slot to next queued vehicle
            next_vehicle = next_waiting_entry.vehicle
            slot.status = SlotStatus.OCCUPIED.value

            new_session = ParkingSession(
                vehicle_id=next_vehicle.id,
                slot_id=slot.id,
                entry_time=now,
                status=SessionStatus.ACTIVE.value
            )
            db.add(new_session)

            # Update in-memory DSA
            parking_lot_dsa.allocate_slot(slot.id, next_vehicle.license_plate)

            auto_allocated_info = AutoAllocatedVehicleInfo(
                vehicle_id=next_vehicle.id,
                license_plate=next_vehicle.license_plate,
                slot_id=slot.id,
                slot_number=slot.slot_number,
                queue_position_was=1,
                allocated_at=now
            )

        db.commit()

        exit_msg = f"Vehicle '{plate}' successfully exited from slot '{slot_number}'."
        if auto_allocated_info:
            exit_msg += f" Slot '{slot_number}' immediately allocated to waiting vehicle '{auto_allocated_info.license_plate}'."

        return VehicleExitResponse(
            status="success",
            message=exit_msg,
            license_plate=plate,
            slot_number=slot_number,
            entry_time=session.entry_time,
            exit_time=now,
            duration_minutes=duration_minutes,
            duration_formatted=format_duration(duration_minutes),
            total_fee=fee,
            rate_applied=rate_applied,
            auto_allocated_to_queued_vehicle=auto_allocated_info
        )

    @staticmethod
    def get_waiting_queue(db: Session) -> List[QueueItemResponse]:
        """
        Returns all vehicles currently in the FIFO waiting queue in arrival order.
        Time Complexity: O(K) where K = queue length.
        """
        queue_records = db.query(WaitingQueue).filter(
            WaitingQueue.status == QueueStatus.WAITING.value
        ).order_by(WaitingQueue.priority.desc(), WaitingQueue.entry_time.asc()).all()

        results = []
        for index, record in enumerate(queue_records):
            plate = record.vehicle.license_plate if record.vehicle else "UNKNOWN"
            vtype = record.vehicle.vehicle_type if record.vehicle else "car"
            results.append(QueueItemResponse(
                position=index + 1,
                db_queue_id=record.id,
                vehicle_id=record.vehicle_id,
                license_plate=plate,
                vehicle_type=vtype,
                priority_rank=record.priority,
                priority_label="Emergency / VIP" if record.priority > 0 else "Standard FIFO",
                entry_time=record.entry_time.isoformat()
            ))
        return results

    @staticmethod
    def get_active_sessions(db: Session) -> List[ActiveSessionResponse]:
        """
        Returns all currently active parking sessions with calculated duration and fee so far.
        """
        now = datetime.now(timezone.utc)
        sessions = db.query(ParkingSession).filter(
            ParkingSession.status == SessionStatus.ACTIVE.value
        ).order_by(ParkingSession.entry_time.desc()).all()

        results = []
        for s in sessions:
            plate = s.vehicle.license_plate if s.vehicle else "UNKNOWN"
            vtype = s.vehicle.vehicle_type if s.vehicle else "car"
            slot_num = s.slot.slot_number if s.slot else f"#{s.slot_id}"
            floor = s.slot.floor if s.slot else 1

            dur_mins, fee_so_far, _ = calculate_parking_charges(s.entry_time, now)

            results.append(ActiveSessionResponse(
                session_id=s.id,
                vehicle_id=s.vehicle_id,
                license_plate=plate,
                vehicle_type=vtype,
                slot_id=s.slot_id,
                slot_number=slot_num,
                floor=floor,
                entry_time=s.entry_time,
                duration_minutes_so_far=dur_mins,
                estimated_fee_so_far=fee_so_far
            ))
        return results

    @staticmethod
    def create_reservation(payload: ReservationRequest, db: Session) -> ReservationResponse:
        """
        Creates a slot reservation:
        - Prevents double reservation or reserving an occupied slot.
        - Sets slot status to RESERVED in SQLite and in-memory Array.
        - Blocks any regular vehicle from receiving this slot.
        """
        plate = payload.license_plate.strip().upper()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=payload.duration_hours)

        # 1. Check if vehicle already has an active session
        if parking_lot_dsa.find_vehicle_slot(plate):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{plate}' is already actively parked."
            )

        # 2. Check if vehicle already has an active reservation
        existing_res = db.query(Reservation).join(Vehicle).filter(
            Vehicle.license_plate == plate,
            Reservation.status == ReservationStatus.ACTIVE.value
        ).first()
        if existing_res:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{plate}' already has an active reservation for slot '{existing_res.slot.slot_number}'."
            )

        # 3. Find target slot
        target_slot = None
        if payload.slot_number:
            slot_num = payload.slot_number.strip().upper()
            target_slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_num).first()
            if not target_slot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Slot '{slot_num}' does not exist."
                )
            if target_slot.status != SlotStatus.AVAILABLE.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Slot '{slot_num}' cannot be reserved because it is currently '{target_slot.status}'."
                )
        else:
            # First-fit available slot
            available_node = parking_lot_dsa.find_available_slot()
            if not available_node:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No available slots found to reserve."
                )
            target_slot = db.query(ParkingSlot).filter(ParkingSlot.id == available_node.id).first()

        # 4. Fetch or create vehicle
        vehicle = db.query(Vehicle).filter(Vehicle.license_plate == plate).first()
        if not vehicle:
            vehicle = Vehicle(
                license_plate=plate,
                vehicle_type=payload.vehicle_type.lower().strip()
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)

        # 5. Lock slot as RESERVED
        target_slot.status = SlotStatus.RESERVED.value

        # Create reservation record
        res_record = Reservation(
            vehicle_id=vehicle.id,
            slot_id=target_slot.id,
            reservation_time=now,
            expires_at=expires_at,
            status=ReservationStatus.ACTIVE.value
        )
        db.add(res_record)
        db.commit()
        db.refresh(res_record)

        # Update in-memory DSA: mark slot as reserved
        parking_lot_dsa.reserve_slot(target_slot.id)

        return ReservationResponse(
            id=res_record.id,
            license_plate=plate,
            slot_id=target_slot.id,
            slot_number=target_slot.slot_number,
            status="reserved",
            reservation_time=now,
            expires_at=expires_at,
            message=f"Slot '{target_slot.slot_number}' successfully reserved for vehicle '{plate}'."
        )

    @staticmethod
    def get_active_reservations(db: Session) -> List[ReservationResponse]:
        """Returns all active reservations."""
        records = db.query(Reservation).filter(
            Reservation.status == ReservationStatus.ACTIVE.value
        ).order_by(Reservation.reservation_time.desc()).all()

        return [
            ReservationResponse(
                id=r.id,
                license_plate=r.vehicle.license_plate if r.vehicle else "UNKNOWN",
                slot_id=r.slot_id,
                slot_number=r.slot.slot_number if r.slot else f"#{r.slot_id}",
                status=r.status,
                reservation_time=r.reservation_time,
                expires_at=r.expires_at,
                message="Active reservation"
            )
            for r in records
        ]

    @staticmethod
    def cancel_reservation(reservation_id: int, db: Session) -> dict:
        """Cancels an active reservation and releases the slot back to AVAILABLE."""
        res_record = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not res_record or res_record.status != ReservationStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active reservation #{reservation_id} not found."
            )

        res_record.status = ReservationStatus.CANCELLED.value
        slot = res_record.slot
        if slot and slot.status == SlotStatus.RESERVED.value:
            slot.status = SlotStatus.AVAILABLE.value
            parking_lot_dsa.cancel_reservation(slot.id)

        db.commit()
        return {
            "message": f"Reservation #{reservation_id} cancelled. Slot '{slot.slot_number}' released to Available.",
            "slot_number": slot.slot_number if slot else None
        }

