import React, { useState } from 'react';
import {
  History,
  Search,
  Receipt,
  Clock
} from 'lucide-react';
import type { ParkingHistoryItem } from '../types';

interface ParkingHistoryViewProps {
  history: ParkingHistoryItem[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const ParkingHistoryView: React.FC<ParkingHistoryViewProps> = ({
  history,
  isLoading,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredHistory = history.filter((item) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase().trim();
    return (
      item.license_plate.toLowerCase().includes(term) ||
      item.slot_number.toLowerCase().includes(term) ||
      item.vehicle_type.toLowerCase().includes(term)
    );
  });

  const totalRevenue = history.reduce((acc, curr) => acc + (curr.total_fee || 0), 0);

  return (
    <div className="page-content">
      {/* Top Summary Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Completed Sessions</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
              <History size={18} />
            </div>
          </div>
          <div className="metric-value">{history.length}</div>
          <div className="metric-footer">Logged in SQLite database</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Total Revenue Collected</span>
            <div className="metric-icon-wrap" style={{ backgroundColor: 'var(--accent-available-bg)', color: 'var(--accent-available)' }}>
              <Receipt size={18} />
            </div>
          </div>
          <div className="metric-value" style={{ color: 'var(--accent-available)' }}>
            ₹{totalRevenue.toFixed(2)}
          </div>
          <div className="metric-footer">Based on ₹20/hr tariff calculation</div>
        </div>
      </div>

      {/* Toolbar / Search */}
      <div className="slots-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, maxWidth: '400px' }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by license plate or slot..."
            className="form-input"
            style={{ width: '100%', fontSize: '13px' }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn-secondary" onClick={onRefresh} disabled={isLoading}>
            <Clock size={14} />
            <span>Refresh Records</span>
          </button>
        </div>
      </div>

      {/* History Data Table */}
      <div className="data-table-container">
        {filteredHistory.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Registration No.</th>
                <th>Slot Number</th>
                <th>Floor</th>
                <th>Vehicle Type</th>
                <th>Entry Timestamp</th>
                <th>Exit Timestamp</th>
                <th>Duration</th>
                <th>Tariff Collected</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item) => (
                <tr key={item.session_id}>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    #{item.session_id}
                  </td>
                  <td>
                    <span className="plate-badge">{item.license_plate}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
                    {item.slot_number}
                  </td>
                  <td>Floor {item.floor}</td>
                  <td style={{ textTransform: 'capitalize' }}>{item.vehicle_type}</td>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {new Date(item.entry_time).toLocaleString()}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
                    {item.exit_time ? new Date(item.exit_time).toLocaleString() : '--'}
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {item.duration_minutes !== null ? `${item.duration_minutes} mins` : '--'}
                  </td>
                  <td style={{ color: item.total_fee ? '#34d399' : 'var(--text-secondary)', fontWeight: 700 }}>
                    {item.total_fee !== null ? `₹${item.total_fee.toFixed(2)}` : 'Free'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="table-empty">
            <History size={36} style={{ margin: '0 auto', opacity: 0.6, marginBottom: '8px' }} />
            <strong>No Parking History Found</strong>
            <p style={{ marginTop: '4px', fontSize: '13px' }}>
              Completed vehicle sessions will automatically appear here upon vehicle exit.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
