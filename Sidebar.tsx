import React from 'react';
import {
  LayoutDashboard,
  CarFront,
  LogIn,
  LogOut,
  CalendarClock,
  ListOrdered,
  History,
  Server,
  Power,
} from 'lucide-react';
import type { NavigationTab, SystemHealth, AuthUser } from '../../types';

interface SidebarProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  health: SystemHealth | null;
  queueCount: number;
  currentUser: AuthUser | null;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  health,
  queueCount,
  currentUser,
  onLogout,
}) => {
  const navItems: { id: NavigationTab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'slots', label: 'Parking Slots', icon: <CarFront size={18} /> },
    { id: 'entry', label: 'Vehicle Entry', icon: <LogIn size={18} /> },
    { id: 'exit', label: 'Vehicle Exit', icon: <LogOut size={18} /> },
    { id: 'reservations', label: 'Reservations', icon: <CalendarClock size={18} /> },
    { id: 'queue', label: 'Queue Management', icon: <ListOrdered size={18} />, badge: queueCount },
    { id: 'history', label: 'Parking History', icon: <History size={18} /> },
  ];

  const isHealthy = health?.status === 'healthy';

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-icon">P</div>
        <div className="logo-text">
          <h1>SmartPark</h1>
          <span>Queue & Slot System</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            id={`nav-item-${item.id}`}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge !== undefined && item.badge > 0 && (
              <span
                style={{
                  backgroundColor: '#f59e0b',
                  color: '#000000',
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '2px 7px',
                  borderRadius: '10px',
                  lineHeight: 1.2
                }}
              >
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        {currentUser && (
          <div className="sidebar-user-card">
            <div className="user-avatar-circle">
              {currentUser.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="user-details" style={{ overflow: 'hidden' }}>
              <span className="user-name" style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {currentUser.full_name}
              </span>
              <span className="user-email" style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {currentUser.email}
              </span>
            </div>
            <button
              id="sidebar-logout-btn"
              type="button"
              className="user-logout-icon-btn"
              onClick={onLogout}
              title="Sign Out of SmartPark"
              aria-label="Sign Out"
            >
              <Power size={14} />
            </button>
          </div>
        )}

        <div className="system-status-pill">
          <div className={`pulse-dot ${isHealthy ? '' : 'error'}`} />
          <div>
            <div style={{ fontWeight: 600, color: '#f8fafc' }}>
              {isHealthy ? 'FastAPI Connected' : 'Connecting to API...'}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Server size={11} />
              <span>SQLite: {health?.database?.status === 'connected' ? 'smartpark.db' : 'Connecting'}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
