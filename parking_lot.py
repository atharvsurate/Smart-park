"""
SmartPark Core DSA Module: Parking Lot Manager
===============================================
Academic / Presentation Documentation:
-------------------------------------
1. Primary Data Structure: Array / List (List[SlotNode])
   - Concept: A contiguous list representing the physical parking slots indexed sequentially.
   - Time Complexity:
     - Sequential First-Fit Slot Search: O(N) where N = total number of slots.
     - Direct Slot Index Access: O(1) by slot ID or index.

2. Auxiliary Data Structure: Hash Map / Dictionary (Dict[str, SlotNode])
   - Concept: Key-value mapping where key = Vehicle License Plate, value = Slot reference.
   - Time Complexity:
     - Lookup vehicle location: O(1) average time.
     - Register vehicle in slot: O(1) average time.
     - Release vehicle from slot: O(1) average time.

3. Space Complexity:
   - Slots Array: O(N) space.
   - Vehicle Lookup Hash Map: O(V) space where V = number of currently parked vehicles (V <= N).
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class SlotNode:
    id: int
    slot_number: str
    slot_type: str        # standard, compact, ev, accessible
    status: str           # available, occupied, reserved
    floor: int
    current_vehicle_plate: Optional[str] = None
    parked_at: Optional[datetime] = None

class ParkingLotDSA:
    """
    In-memory DSA representation of the parking lot slots and fast lookup map.
    Synchronizes with SQLite persistent storage on operations.
    """
    def __init__(self):
        # 1. Array / List of all parking slots (Ordered layout)
        self.slots: List[SlotNode] = []
        
        # 2. Hash Map for O(1) active vehicle plate to slot lookup
        self.plate_to_slot_map: Dict[str, SlotNode] = {}

    def load_from_db_records(self, db_slots: list, active_sessions: list = None) -> None:
        """
        Reconstructs the in-memory List and Hash Map from SQLite database records.
        Time Complexity: O(N + S) where N is slot count and S is active sessions count.
        """
        self.slots.clear()
        self.plate_to_slot_map.clear()

        session_map = {}
        if active_sessions:
            for session in active_sessions:
                # Map slot_id to vehicle license plate
                plate = session.vehicle.license_plate if session.vehicle else None
                if plate:
                    session_map[session.slot_id] = (plate, session.entry_time)

        for s in db_slots:
            plate_info = session_map.get(s.id, (None, None))
            node = SlotNode(
                id=s.id,
                slot_number=s.slot_number,
                slot_type=s.slot_type,
                status=s.status,
                floor=s.floor,
                current_vehicle_plate=plate_info[0],
                parked_at=plate_info[1]
            )
            self.slots.append(node)
            if node.current_vehicle_plate:
                self.plate_to_slot_map[node.current_vehicle_plate.upper()] = node

    def find_available_slot(self, slot_type: Optional[str] = None) -> Optional[SlotNode]:
        """
        Algorithm: First-Fit Slot Allocation
        Traverses the Array of slots sequentially to find the first matching available slot.
        Time Complexity:
          - Best Case: O(1) if the first slot is available.
          - Worst Case: O(N) if the last slot is available or all are full.
        Space Complexity: O(1) auxiliary space.
        """
        for slot in self.slots:
            if slot.status == "available":
                if slot_type is None or slot.slot_type == slot_type:
                    return slot
        return None

    def find_slot_by_id(self, slot_id: int) -> Optional[SlotNode]:
        """
        Searches slot array by unique ID.
        Time Complexity: O(N) linear search over array.
        """
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        return None

    def find_slot_by_plate(self, plate: str) -> Optional[SlotNode]:
        """
        Algorithm: Hash Map Lookup
        Quickly identifies which slot a vehicle is parked in without looping over slots.
        Time Complexity: O(1) average time complexity.
        """
        return self.plate_to_slot_map.get(plate.upper().strip())

    def find_vehicle_slot(self, plate: str) -> Optional[SlotNode]:
        """Alias for find_slot_by_plate. Time Complexity: O(1)."""
        return self.find_slot_by_plate(plate)


    def allocate_slot(self, slot_id: int, vehicle_plate: str) -> bool:
        """
        Marks slot as occupied and updates the Hash Map.
        Time Complexity: O(N) to locate slot + O(1) to update status and hash map.
        """
        slot = self.find_slot_by_id(slot_id)
        if slot and slot.status == "available":
            slot.status = "occupied"
            slot.current_vehicle_plate = vehicle_plate.upper().strip()
            slot.parked_at = datetime.now(timezone.utc)
            self.plate_to_slot_map[slot.current_vehicle_plate] = slot
            return True
        return False

    def release_slot(self, slot_id: int) -> Optional[SlotNode]:
        """
        Releases an occupied slot and deletes the plate from the Hash Map.
        Time Complexity: O(N) to find slot + O(1) hash map deletion.
        """
        slot = self.find_slot_by_id(slot_id)
        if slot and slot.status == "occupied":
            if slot.current_vehicle_plate and slot.current_vehicle_plate in self.plate_to_slot_map:
                del self.plate_to_slot_map[slot.current_vehicle_plate]
            slot.status = "available"
            slot.current_vehicle_plate = None
            slot.parked_at = None
            return slot
        return None

    def reserve_slot(self, slot_id: int) -> bool:
        """
        Reserves an available slot.
        Time Complexity: O(N) array search.
        """
        slot = self.find_slot_by_id(slot_id)
        if slot and slot.status == "available":
            slot.status = "reserved"
            return True
        return False

    def cancel_reservation(self, slot_id: int) -> bool:
        slot = self.find_slot_by_id(slot_id)
        if slot and slot.status == "reserved":
            slot.status = "available"
            return True
        return False

    def get_summary(self) -> dict:
        """
        Calculates aggregate slot metrics.
        Time Complexity: O(N) single pass over the slot array.
        """
        total = len(self.slots)
        available = 0
        occupied = 0
        reserved = 0

        for slot in self.slots:
            if slot.status == "available":
                available += 1
            elif slot.status == "occupied":
                occupied += 1
            elif slot.status == "reserved":
                reserved += 1

        return {
            "total_slots": total,
            "available_slots": available,
            "occupied_slots": occupied,
            "reserved_slots": reserved
        }

# Global singleton instance for in-memory DSA operations
parking_lot_dsa = ParkingLotDSA()
