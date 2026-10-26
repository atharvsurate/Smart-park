"""
SmartPark Core DSA Module: Waiting Queue Manager
=================================================
Academic / Presentation Documentation:
-------------------------------------
1. Primary Data Structure: FIFO Queue (collections.deque)
   - Concept: First-In, First-Out queue maintaining strict arrival order for waiting vehicles.
   - Operations:
     - Enqueue (append): O(1) amortized time.
     - Dequeue (popleft): O(1) time.
     - Peek front: O(1) time.
     - Size check: O(1) time.

2. Secondary Data Structure: Priority Queue (Min-Heap using heapq)
   - Concept: Binary heap where emergency vehicles (ambulance, security) or VIP vehicles
     bypass the standard queue.
   - Priority tuple format: (priority_rank, arrival_timestamp, queue_item)
     where lower priority_rank has higher urgency (e.g. 0 = Emergency, 1 = VIP, 2 = Standard).
   - Operations:
     - Heappush: O(log K) time where K = number of queued elements.
     - Heappop: O(log K) time.
     - Peek top: O(1) time.

3. Space Complexity:
   - O(K) space where K = number of waiting vehicles in the queue.
"""

from collections import deque
import heapq
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

@dataclass(order=True)
class QueuedVehicle:
    # priority_rank: 0 for Emergency/VIP, 1 for Standard
    priority_rank: int
    entry_timestamp: float
    # Non-comparable fields
    vehicle_id: int = field(compare=False)
    license_plate: str = field(compare=False)
    vehicle_type: str = field(compare=False)
    entry_time_str: str = field(compare=False)
    db_queue_id: Optional[int] = field(default=None, compare=False)

class WaitingQueueDSA:
    """
    Manages both a standard FIFO queue and an optional Priority Heap Queue
    for vehicle queue scheduling when all parking slots are full.
    """
    def __init__(self):
        # 1. Pure FIFO Queue for standard vehicle arrivals
        self.fifo_queue: deque = deque()

        # 2. Priority Min-Heap Queue for priority/emergency arrivals
        self.priority_heap: List[QueuedVehicle] = []

    def load_from_db_records(self, db_queue_items: list) -> None:
        """
        Reconstructs the queue from SQLite records on server startup.
        Time Complexity: O(K log K) for heap push or O(K) for deque.
        """
        self.fifo_queue.clear()
        self.priority_heap.clear()

        # Sort by entry_time ascending to maintain arrival order
        sorted_items = sorted(db_queue_items, key=lambda x: x.entry_time)

        for item in sorted_items:
            plate = item.vehicle.license_plate if item.vehicle else "UNKNOWN"
            vtype = item.vehicle.vehicle_type if item.vehicle else "car"
            timestamp = item.entry_time.timestamp()
            time_str = item.entry_time.isoformat()

            queued = QueuedVehicle(
                priority_rank=0 if item.priority > 0 else 1,
                entry_timestamp=timestamp,
                vehicle_id=item.vehicle_id,
                license_plate=plate,
                vehicle_type=vtype,
                entry_time_str=time_str,
                db_queue_id=item.id
            )

            # Insert into FIFO queue
            self.fifo_queue.append(queued)
            # Also keep heap updated
            heapq.heappush(self.priority_heap, queued)

    def enqueue_fifo(self, vehicle_id: int, license_plate: str, vehicle_type: str, db_queue_id: Optional[int] = None) -> QueuedVehicle:
        """
        Algorithm: FIFO Queue Enqueue
        Appends the vehicle to the tail of the waiting line.
        Time Complexity: O(1) amortized.
        """
        now = datetime.now(timezone.utc)
        queued = QueuedVehicle(
            priority_rank=1,
            entry_timestamp=now.timestamp(),
            vehicle_id=vehicle_id,
            license_plate=license_plate.upper().strip(),
            vehicle_type=vehicle_type,
            entry_time_str=now.isoformat(),
            db_queue_id=db_queue_id
        )
        self.fifo_queue.append(queued)
        heapq.heappush(self.priority_heap, queued)
        return queued

    def enqueue_priority(self, vehicle_id: int, license_plate: str, vehicle_type: str, priority_level: int = 0, db_queue_id: Optional[int] = None) -> QueuedVehicle:
        """
        Algorithm: Priority Queue Heap Push
        Inserts emergency/VIP vehicle into the min-heap so it is served first.
        Time Complexity: O(log K) where K = queue length.
        """
        now = datetime.now(timezone.utc)
        queued = QueuedVehicle(
            priority_rank=priority_level,  # 0 is top priority
            entry_timestamp=now.timestamp(),
            vehicle_id=vehicle_id,
            license_plate=license_plate.upper().strip(),
            vehicle_type=vehicle_type,
            entry_time_str=now.isoformat(),
            db_queue_id=db_queue_id
        )
        heapq.heappush(self.priority_heap, queued)
        # Also push to FIFO (at front if priority 0)
        if priority_level == 0:
            self.fifo_queue.appendleft(queued)
        else:
            self.fifo_queue.append(queued)
        return queued

    def dequeue(self) -> Optional[QueuedVehicle]:
        """
        Algorithm: Queue Dequeue (Dispatches next vehicle to newly freed slot)
        Time Complexity: O(1) from deque.
        """
        if not self.fifo_queue:
            return None
        item = self.fifo_queue.popleft()
        # Clean from heap if present
        if item in self.priority_heap:
            self.priority_heap.remove(item)
            heapq.heapify(self.priority_heap)
        return item

    def peek(self) -> Optional[QueuedVehicle]:
        """
        Algorithm: Queue Peek (Inspect front vehicle without removal)
        Time Complexity: O(1).
        """
        return self.fifo_queue[0] if self.fifo_queue else None

    def size(self) -> int:
        """Time Complexity: O(1)."""
        return len(self.fifo_queue)

    def is_empty(self) -> bool:
        """Time Complexity: O(1)."""
        return len(self.fifo_queue) == 0

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Returns list of vehicles currently in queue in order of service.
        Time Complexity: O(K) where K = queue length.
        """
        result = []
        for index, item in enumerate(self.fifo_queue):
            result.append({
                "position": index + 1,
                "db_queue_id": item.db_queue_id,
                "vehicle_id": item.vehicle_id,
                "license_plate": item.license_plate,
                "vehicle_type": item.vehicle_type,
                "priority_rank": item.priority_rank,
                "priority_label": "Emergency / VIP" if item.priority_rank == 0 else "Standard FIFO",
                "entry_time": item.entry_time_str
            })
        return result

# Global singleton queue manager instance
waiting_queue_dsa = WaitingQueueDSA()
