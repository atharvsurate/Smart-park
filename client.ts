import type {
  ParkingSlot,
  DashboardSummary,
  SystemHealth,
  VehicleEntryPayload,
  VehicleEntryResult,
  VehicleExitResult,
  QueueItem,
  ActiveSession,
  ParkingHistoryItem,
  ReservationItem,
  AuthUser,
  AuthResponse,
} from '../types';

const API_BASE = '/api';
const TOKEN_KEY = 'smartpark_auth_token';
const USER_KEY = 'smartpark_auth_user';

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredAuth(token: string, user: AuthUser): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (err) {
    console.error('Failed to store auth credentials:', err);
  }
}

export function clearStoredAuth(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch (err) {
    console.error('Failed to clear auth credentials:', err);
  }
}

/**
 * Parses FastAPI HTTP error responses into human-readable error messages.
 */
async function handleApiError(res: Response, defaultMessage: string): Promise<never> {
  let errorMessage = defaultMessage;
  try {
    const errorBody = await res.json();
    if (errorBody && errorBody.detail) {
      errorMessage = typeof errorBody.detail === 'string'
        ? errorBody.detail
        : JSON.stringify(errorBody.detail);
    }
  } catch {
    errorMessage = `${defaultMessage} (HTTP ${res.status})`;
  }
  throw new Error(errorMessage);
}

/**
 * Authenticated Fetch wrapper that automatically appends the Bearer token
 * and triggers an unauthorized event on HTTP 401.
 */
async function authFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  const headers = new Headers(init.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const res = await fetch(input, {
    ...init,
    headers,
  });

  if (res.status === 401) {
    clearStoredAuth();
    window.dispatchEvent(new CustomEvent('smartpark:unauthorized'));
  }

  return res;
}

/* =========================================================
   AUTHENTICATION ENDPOINTS
   ========================================================= */

export async function registerUser(payload: {
  full_name: string;
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return handleApiError(res, 'Registration failed');
  }
  const data: AuthResponse = await res.json();
  setStoredAuth(data.access_token, data.user);
  return data;
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return handleApiError(res, 'Login failed');
  }
  const data: AuthResponse = await res.json();
  setStoredAuth(data.access_token, data.user);
  return data;
}

export async function getAuthProfile(): Promise<AuthUser> {
  const res = await authFetch(`${API_BASE}/auth/me`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch user profile');
  }
  return res.json();
}

/* =========================================================
   PARKING & DASHBOARD ENDPOINTS (PROTECTED)
   ========================================================= */

export async function getSystemHealth(): Promise<SystemHealth> {
  // Public endpoint
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    return handleApiError(res, 'Health check failed');
  }
  return res.json();
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const res = await authFetch(`${API_BASE}/dashboard/summary`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch dashboard summary');
  }
  return res.json();
}

export async function getParkingSlots(params?: {
  status?: string;
  slot_type?: string;
  floor?: number;
}): Promise<ParkingSlot[]> {
  const query = new URLSearchParams();
  if (params?.status) query.append('status_filter', params.status);
  if (params?.slot_type) query.append('slot_type', params.slot_type);
  if (params?.floor !== undefined) query.append('floor', params.floor.toString());

  const url = `${API_BASE}/slots${query.toString() ? `?${query.toString()}` : ''}`;
  const res = await authFetch(url);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch parking slots');
  }
  return res.json();
}

export async function createParkingSlot(data: {
  slot_number: string;
  slot_type: string;
  floor: number;
}): Promise<ParkingSlot> {
  const res = await authFetch(`${API_BASE}/slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    return handleApiError(res, 'Failed to create parking slot');
  }
  return res.json();
}

export async function seedParkingSlots(): Promise<{ message: string; slot_count: number }> {
  const res = await authFetch(`${API_BASE}/slots/seed-10`, {
    method: 'POST',
  });
  if (!res.ok) {
    return handleApiError(res, 'Failed to seed parking slots');
  }
  return res.json();
}

export async function registerVehicleEntry(payload: VehicleEntryPayload): Promise<VehicleEntryResult> {
  const res = await authFetch(`${API_BASE}/vehicles/entry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    return handleApiError(res, 'Vehicle entry registration failed');
  }
  return res.json();
}

export async function processVehicleExit(license_plate: string): Promise<VehicleExitResult> {
  const res = await authFetch(`${API_BASE}/vehicles/exit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ license_plate }),
  });
  if (!res.ok) {
    return handleApiError(res, 'Vehicle exit processing failed');
  }
  return res.json();
}

export async function getWaitingQueue(): Promise<QueueItem[]> {
  const res = await authFetch(`${API_BASE}/queue`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch waiting queue');
  }
  return res.json();
}

export async function getActiveSessions(): Promise<ActiveSession[]> {
  const res = await authFetch(`${API_BASE}/sessions/active`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch active parking sessions');
  }
  return res.json();
}

export async function getParkingHistory(limit: number = 50): Promise<ParkingHistoryItem[]> {
  const res = await authFetch(`${API_BASE}/sessions/history?limit=${limit}`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch parking history');
  }
  return res.json();
}

export async function createReservation(data: {
  license_plate: string;
  slot_number?: string;
  vehicle_type?: string;
  duration_hours?: number;
}): Promise<ReservationItem> {
  const res = await authFetch(`${API_BASE}/reservations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    return handleApiError(res, 'Slot reservation failed');
  }
  return res.json();
}

export async function getReservations(): Promise<ReservationItem[]> {
  const res = await authFetch(`${API_BASE}/reservations`);
  if (!res.ok) {
    return handleApiError(res, 'Failed to fetch reservations');
  }
  return res.json();
}

export async function cancelReservation(reservationId: number): Promise<{ message: string; slot_number: string }> {
  const res = await authFetch(`${API_BASE}/reservations/${reservationId}/cancel`, {
    method: 'POST',
  });
  if (!res.ok) {
    return handleApiError(res, 'Failed to cancel reservation');
  }
  return res.json();
}
