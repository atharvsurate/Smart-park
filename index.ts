export type SlotType = 'standard' | 'compact' | 'ev' | 'accessible';
export type SlotStatus = 'available' | 'occupied' | 'reserved';

export interface ParkingSlot {
  id: number;
  slot_number: string;
  slot_type: SlotType;
  status: SlotStatus;
  floor: number;
  current_vehicle_plate?: string | null;
  parked_at?: string | null;
  created_at?: string | null;
}

export interface DsaMetrics {
  slots_array_length: number;
  hash_map_active_plates: number;
  fifo_queue_length: number;
  first_fit_time_complexity: string;
  hash_map_lookup_complexity: string;
  queue_enqueue_complexity: string;
}

export interface DashboardSummary {
  total_slots: number;
  available_slots: number;
  occupied_slots: number;
  reserved_slots: number;
  waiting_queue_count: number;
  active_sessions_count: number;
  dsa_metrics: DsaMetrics;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  service: string;
  version: string;
  environment: string;
  database: {
    status: string;
    engine: string;
    db_file_exists?: boolean;
    error?: string;
  };
  dsa_engine: {
    status: string;
    structures: Record<string, { type: string; length?: number; entries?: number }>;
  };
  modules: Record<string, { status: string; description: string }>;
}

export interface VehicleEntryPayload {
  license_plate: string;
  vehicle_type: string;
  owner_name?: string;
  contact_number?: string;
  is_priority?: boolean;
}

export interface VehicleEntryResult {
  status: 'allocated' | 'queued';
  message: string;
  license_plate: string;
  vehicle_type: string;
  slot_id?: number | null;
  slot_number?: string | null;
  queue_position?: number | null;
  entry_time: string;
}

export interface AutoAllocatedQueueInfo {
  vehicle_id: number;
  license_plate: string;
  slot_id: number;
  slot_number: string;
  queue_position_was: number;
  allocated_at: string;
}

export interface VehicleExitResult {
  status: string;
  message: string;
  license_plate: string;
  slot_number: string;
  entry_time: string;
  exit_time: string;
  duration_minutes: number;
  duration_formatted: string;
  total_fee: number;
  rate_applied: string;
  auto_allocated_to_queued_vehicle?: AutoAllocatedQueueInfo | null;
}

export interface QueueItem {
  position: number;
  db_queue_id?: number | null;
  vehicle_id: number;
  license_plate: string;
  vehicle_type: string;
  priority_rank: number;
  priority_label: string;
  entry_time: string;
}

export interface ActiveSession {
  session_id: number;
  vehicle_id: number;
  license_plate: string;
  vehicle_type: string;
  slot_id: number;
  slot_number: string;
  floor: number;
  entry_time: string;
  duration_minutes_so_far: number;
  estimated_fee_so_far: number;
}

export interface ParkingHistoryItem {
  session_id: number;
  license_plate: string;
  vehicle_type: string;
  slot_number: string;
  floor: number;
  entry_time: string;
  exit_time: string | null;
  duration_minutes: number | null;
  total_fee: number | null;
}

export interface ReservationItem {
  id: number;
  license_plate: string;
  slot_id: number;
  slot_number: string;
  status: string;
  reservation_time: string;
  expires_at: string;
  message: string;
}

export type NavigationTab =
  | 'dashboard'
  | 'slots'
  | 'entry'
  | 'exit'
  | 'reservations'
  | 'queue'
  | 'history';

export interface AuthUser {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

