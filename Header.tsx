import React, { useState, useEffect } from 'react';
import { RefreshCw, Clock, LogOut } from 'lucide-react';
import type { NavigationTab, SystemHealth, AuthUser } from '../../types';

interface HeaderProps {
  activeTab: NavigationTab;
  health: SystemHealth | null;
  onRefresh: () => void;
  isLoading: boolean;
  currentUser?: AuthUser | null;
  onLogout?: () => void;
}

const TAB_TITLES: Record<NavigationTab, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Dashboard Overview',
    subtitle: 'Real-time parking capacity, slot telemetry, and live queue status',
  },
  slots: {
    title: 'Parking Slots Management',
    subtitle: 'Visual slot layout, status indicators, and current vehicle allocations',
  },
  entry: {
    title: 'Vehicle Entry',
    subtitle: 'Register vehicle arrival, allocate available slot, or enqueue into FIFO waiting line',
  },
  exit: {
    title: 'Vehicle Exit & Billing',
    subtitle: 'Process vehicle departure, calculate duration & parking charges, and dispatch waiting queue',
  },
  reservations: {
    title: 'Slot Reservations',
    subtitle: 'Pre-book parking slots in advance and prevent conflicting allocations',
  },
  queue: {
    title: 'Queue Management',
    subtitle: 'FIFO waiting queue for vehicles awaiting parking slot vacancy',
  },
  history: {
    title: 'Parking History',
    subtitle: 'Comprehensive audit log of past parking sessions, duration, and collected charges',
  },
};

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onRefresh,
  isLoading,
  currentUser,
  onLogout,
}) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const meta = TAB_TITLES[activeTab] || { title: 'SmartPark', subtitle: '' };

  return (
    <header className="top-header">
      <div className="header-title-section">
        <h2>{meta.title}</h2>
        <p>{meta.subtitle}</p>
      </div>

      <div className="header-actions">
        <div className="clock-display" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={13} style={{ color: '#818cf8' }} />
          <span>{timeStr || 'Live'}</span>
        </div>

        <button
          id="btn-refresh-data"
          className="btn-secondary"
          onClick={onRefresh}
          disabled={isLoading}
          title="Refresh real-time data"
        >
          <RefreshCw size={14} className={isLoading ? 'spin-icon' : ''} />
          <span>{isLoading ? 'Updating...' : 'Refresh'}</span>
        </button>

        {onLogout && (
          <button
            id="btn-header-logout"
            className="btn-secondary"
            onClick={onLogout}
            title={currentUser ? `Signed in as ${currentUser.email}` : 'Sign Out'}
            style={{ color: '#f43f5e', borderColor: 'rgba(244, 63, 94, 0.3)' }}
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </header>
  );
};
