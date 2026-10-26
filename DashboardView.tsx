import React from 'react';
import {
  CarFront,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  LogIn,
  LogOut,
  CalendarClock
} from 'lucide-react';
import type { DashboardSummary, ActiveSession, NavigationTab } from '../types';

interface DashboardViewProps {
  summary: DashboardSummary | null;
  activeSessions: ActiveSession[];
  onNavigate: (tab: NavigationTab) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary,
  activeSessions,
  onNavigate,
}) => {
  return (
    <div className="page-content">
      {/* Metrics Row: Actual backend values */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Total Parking Slots</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
              <Layers size={18} />
            </div>
          </div>
          <div className="metric-value">{summary ? summary.total_slots : '--'}</div>
          <div className="metric-footer">Configured physical capacity</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Available Slots</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'var(--accent-available-bg)', color: 'var(--accent-available)' }}>
              <CheckCircle2 size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-available)' }}>
            {summary ? summary.available_slots : '--'}
          </div>
          <div className="metric-footer">Ready for immediate allocation</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Occupied Slots</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'var(--accent-occupied-bg)', color: 'var(--accent-occupied)' }}>
              <XCircle size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-occupied)' }}>
            {summary ? summary.occupied_slots : '--'}
          </div>
          <div className="metric-footer">Currently parked vehicles</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Reserved Slots</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'var(--accent-reserved-bg)', color: 'var(--accent-reserved)' }}>
              <CalendarClock size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-reserved)' }}>
            {summary ? summary.reserved_slots : 0}
          </div>
          <div className="metric-footer">Active pre-bookings</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Vehicles in Queue</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
              <Clock size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: '#f59e0b' }}>
            {summary ? summary.waiting_queue_count : 0}
          </div>
          <div className="metric-footer">FIFO waiting line order</div>
        </div>
      </div>

      {/* Quick Operations Launch Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        <button
          className="btn-primary"
          style={{ justifyContent: 'center', padding: '14px', fontSize: '14px' }}
          onClick={() => onNavigate('entry')}
        >
          <LogIn size={16} />
          <span>Vehicle Entry Form</span>
        </button>

        <button
          className="btn-secondary"
          style={{ justifyContent: 'center', padding: '14px', fontSize: '14px' }}
          onClick={() => onNavigate('exit')}
        >
          <LogOut size={16} />
          <span>Vehicle Exit & Billing</span>
        </button>

        <button
          className="btn-secondary"
          style={{ justifyContent: 'center', padding: '14px', fontSize: '14px' }}
          onClick={() => onNavigate('slots')}
        >
          <CarFront size={16} />
          <span>Inspect Slot Grid</span>
        </button>
      </div>

      {/* Active Sessions Live Table */}
      <div className="data-table-container">
        <div style={{ padding: '18px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Actively Parked Vehicles</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Real-time records from SQLite <code>parking_sessions</code>
            </p>
          </div>
          <span style={{ fontSize: '12px', color: '#818cf8', fontWeight: 600 }}>
            {activeSessions.length} Active
          </span>
        </div>

        {activeSessions.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Registration No.</th>
                <th>Slot Number</th>
                <th>Floor</th>
                <th>Vehicle Type</th>
                <th>Entry Timestamp</th>
                <th>Elapsed Duration</th>
                <th>Estimated Fee</th>
              </tr>
            </thead>
            <tbody>
              {activeSessions.map((session) => (
                <tr key={session.session_id}>
                  <td>
                    <span className="plate-badge">{session.license_plate}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                    {session.slot_number}
                  </td>
                  <td>Floor {session.floor}</td>
                  <td style={{ textTransform: 'capitalize' }}>{session.vehicle_type}</td>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {new Date(session.entry_time).toLocaleTimeString()}
                  </td>
                  <td style={{ fontWeight: 600, color: '#e2e8f0' }}>
                    {session.duration_minutes_so_far} mins
                  </td>
                  <td style={{ color: session.estimated_fee_so_far > 0 ? '#34d399' : 'var(--text-muted)', fontWeight: 600 }}>
                    ₹{session.estimated_fee_so_far.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="table-empty">
            No vehicles currently parked. All slots are ready for allocation.
          </div>
        )}
      </div>

      {/* DSA Academic Engine Section */}
      <div className="dsa-info-card">
        <div className="dsa-header">
          <h3>Core Data Structures & Algorithms (DSA) Engine</h3>
          <span className="dsa-pill">Deterministic Core</span>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Real-time state and theoretical time complexities operating across the application:
        </p>
        <div className="dsa-grid">
          <div className="dsa-item">
            <h4>
              <span>Array / List (Slots)</span>
              <span className="complexity-tag">{summary?.dsa_metrics?.first_fit_time_complexity || 'O(N)'}</span>
            </h4>
            <p>
              Stores physical slots indexed sequentially. Implements <strong>First-Fit Allocation</strong> to find the first matching available slot.
            </p>
            <div style={{ marginTop: '10px', fontSize: '11px', color: '#94a3b8' }}>
              Array size: <strong>{summary?.dsa_metrics?.slots_array_length ?? 10} slots</strong>
            </div>
          </div>

          <div className="dsa-item">
            <h4>
              <span>Hash Map (Lookup)</span>
              <span className="complexity-tag">{summary?.dsa_metrics?.hash_map_lookup_complexity || 'O(1)'}</span>
            </h4>
            <p>
              Maps <code>License Plate &rarr; SlotNode</code> for constant-time lookups during departure and duplicate-checking.
            </p>
            <div style={{ marginTop: '10px', fontSize: '11px', color: '#94a3b8' }}>
              Mapped entries: <strong>{summary?.dsa_metrics?.hash_map_active_plates ?? activeSessions.length} active plates</strong>
            </div>
          </div>

          <div className="dsa-item">
            <h4>
              <span>FIFO Waiting Queue</span>
              <span className="complexity-tag">{summary?.dsa_metrics?.queue_enqueue_complexity || 'O(1)'}</span>
            </h4>
            <p>
              Enqueues arrivals when capacity is saturated. Automatically dispatches the next queued vehicle when an occupied slot is released.
            </p>
            <div style={{ marginTop: '10px', fontSize: '11px', color: '#94a3b8' }}>
              Waiting in line: <strong>{summary?.dsa_metrics?.fifo_queue_length ?? 0} vehicles</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
