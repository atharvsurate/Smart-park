import React from 'react';
import {
  ListOrdered,
  Clock,
  LogIn
} from 'lucide-react';
import type { QueueItem, NavigationTab } from '../types';

interface QueueManagementViewProps {
  queue: QueueItem[];
  isLoading: boolean;
  onRefresh: () => void;
  onNavigate: (tab: NavigationTab) => void;
}

export const QueueManagementView: React.FC<QueueManagementViewProps> = ({
  queue,
  isLoading,
  onRefresh,
  onNavigate,
}) => {
  return (
    <div className="page-content">
      {/* Overview Status Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', background: 'var(--bg-card)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ padding: '12px', borderRadius: '10px', backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
            <ListOrdered size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>
              FIFO Waiting Line ({queue.length} Vehicles Waiting)
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Vehicles enter the queue when all slots are full and are automatically dispatched on slot departure.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn-secondary" onClick={onRefresh} disabled={isLoading}>
            <Clock size={14} />
            <span>Refresh Queue</span>
          </button>
          <button className="btn-primary" onClick={() => onNavigate('entry')}>
            <LogIn size={14} />
            <span>Enqueue Vehicle</span>
          </button>
        </div>
      </div>

      {/* Queue Data Table */}
      <div className="data-table-container">
        {queue.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '90px' }}>Queue Position</th>
                <th>Registration No.</th>
                <th>Vehicle Type</th>
                <th>Priority Category</th>
                <th>Arrival Timestamp</th>
                <th>Waiting Status</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((item) => (
                <tr key={item.position}>
                  <td>
                    <span
                      style={{
                        display: 'inline-block',
                        width: '28px',
                        height: '28px',
                        borderRadius: '50%',
                        backgroundColor: item.position === 1 ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                        color: '#ffffff',
                        textAlign: 'center',
                        lineHeight: '28px',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)'
                      }}
                    >
                      {item.position}
                    </span>
                  </td>
                  <td>
                    <span className="plate-badge">{item.license_plate}</span>
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>{item.vehicle_type}</td>
                  <td>
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '3px 8px',
                        borderRadius: '6px',
                        fontWeight: 600,
                        backgroundColor: item.priority_rank > 0 ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        color: item.priority_rank > 0 ? '#fda4af' : 'var(--text-secondary)'
                      }}
                    >
                      {item.priority_label}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {new Date(item.entry_time).toLocaleTimeString()}
                  </td>
                  <td>
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px',
                        color: item.position === 1 ? '#34d399' : '#fbbf24',
                        fontWeight: 600
                      }}
                    >
                      <span
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: item.position === 1 ? 'var(--accent-available)' : '#fbbf24'
                        }}
                      />
                      {item.position === 1 ? 'Next to be Allocated' : 'Waiting in Order'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="table-empty">
            <div style={{ color: 'var(--accent-available)', marginBottom: '8px' }}>
              <Clock size={36} style={{ margin: '0 auto', opacity: 0.6 }} />
            </div>
            <strong>Waiting Queue is Empty</strong>
            <p style={{ marginTop: '4px', fontSize: '13px' }}>
              All arriving vehicles can be allocated parking slots immediately.
            </p>
          </div>
        )}
      </div>

      {/* Presentation / DSA Explanation Footer */}
      <div style={{ padding: '16px 20px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: '10px', border: '1px solid var(--border-subtle)', fontSize: '13px', color: 'var(--text-secondary)' }}>
        <strong>Data Structure In Action:</strong> The waiting queue is maintained using <code>collections.deque</code> in Python backend memory and synchronized with the SQLite <code>waiting_queue</code> table. Enqueue and dequeue operations execute with <strong>O(1)</strong> time complexity.
      </div>
    </div>
  );
};
