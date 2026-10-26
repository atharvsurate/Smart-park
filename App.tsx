import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardView } from './views/DashboardView';
import { ParkingSlotsView } from './views/ParkingSlotsView';
import { VehicleEntryView } from './views/VehicleEntryView';
import { VehicleExitView } from './views/VehicleExitView';
import { QueueManagementView } from './views/QueueManagementView';
import { ParkingHistoryView } from './views/ParkingHistoryView';
import { ReservationsView } from './views/ReservationsView';
import { LoginView } from './views/LoginView';
import { RegisterView } from './views/RegisterView';
import type {
  NavigationTab,
  ParkingSlot,
  DashboardSummary,
  SystemHealth,
  ActiveSession,
  QueueItem,
  ParkingHistoryItem,
  ReservationItem,
  AuthUser,
} from './types';
import {
  getSystemHealth,
  getDashboardSummary,
  getParkingSlots,
  getActiveSessions,
  getWaitingQueue,
  getParkingHistory,
  getReservations,
  getStoredToken,
  getStoredUser,
  clearStoredAuth,
} from './api/client';
import { CheckCircle, AlertTriangle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(getStoredUser());
  const [authToken, setAuthToken] = useState<string | null>(getStoredToken());
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const [activeTab, setActiveTab] = useState<NavigationTab>('dashboard');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [slots, setSlots] = useState<ParkingSlot[]>([]);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [history, setHistory] = useState<ParkingHistoryItem[]>([]);
  const [reservations, setReservations] = useState<ReservationItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  }, []);

  const handleLogout = useCallback(() => {
    clearStoredAuth();
    setCurrentUser(null);
    setAuthToken(null);
    setAuthMode('login');
    setSummary(null);
    setSlots([]);
    setActiveSessions([]);
    setQueue([]);
    setHistory([]);
    setReservations([]);
    showToast('You have been logged out successfully.', 'success');
  }, [showToast]);

  // Listen to 401 unauthorized events from API client
  useEffect(() => {
    const handleUnauthorized = () => {
      clearStoredAuth();
      setCurrentUser(null);
      setAuthToken(null);
      setAuthMode('login');
      showToast('Session expired or unauthorized. Please log in again.', 'error');
    };
    window.addEventListener('smartpark:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('smartpark:unauthorized', handleUnauthorized);
  }, [showToast]);

  const loadAllData = useCallback(async () => {
    // Only load data if an active authentication token exists
    if (!getStoredToken()) {
      return;
    }

    setIsLoading(true);
    try {
      const [healthData, summaryData, slotsData, sessionsData, queueData, historyData, reservationsData] =
        await Promise.all([
          getSystemHealth().catch((err) => {
            console.warn('Backend health check error:', err);
            return null;
          }),
          getDashboardSummary().catch((err) => {
            console.warn('Dashboard summary error:', err);
            return null;
          }),
          getParkingSlots().catch((err) => {
            console.warn('Slots fetch error:', err);
            return [];
          }),
          getActiveSessions().catch((err) => {
            console.warn('Active sessions fetch error:', err);
            return [];
          }),
          getWaitingQueue().catch((err) => {
            console.warn('Queue fetch error:', err);
            return [];
          }),
          getParkingHistory().catch((err) => {
            console.warn('History fetch error:', err);
            return [];
          }),
          getReservations().catch((err) => {
            console.warn('Reservations fetch error:', err);
            return [];
          }),
        ]);

      setHealth(healthData);
      setSummary(summaryData);
      setSlots(slotsData);
      setActiveSessions(sessionsData);
      setQueue(queueData);
      setHistory(historyData);
      setReservations(reservationsData);
    } catch (error: any) {
      console.error('Data loading error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authToken && currentUser) {
      loadAllData();
      // Auto-refresh every 12 seconds
      const interval = setInterval(loadAllData, 12000);
      return () => clearInterval(interval);
    }
  }, [authToken, currentUser, loadAllData]);

  const handleOperationSuccess = useCallback(() => {
    loadAllData();
    showToast('Parking operation completed successfully!', 'success');
  }, [loadAllData, showToast]);

  const handleAuthSuccess = useCallback((user: AuthUser, token: string) => {
    setCurrentUser(user);
    setAuthToken(token);
    showToast(`Welcome to SmartPark, ${user.full_name}!`, 'success');
  }, [showToast]);

  // Unauthenticated State: Render Login or Registration view
  if (!authToken || !currentUser) {
    return (
      <>
        {authMode === 'login' ? (
          <LoginView
            onLoginSuccess={handleAuthSuccess}
            onNavigateToRegister={() => setAuthMode('register')}
          />
        ) : (
          <RegisterView
            onRegisterSuccess={handleAuthSuccess}
            onNavigateToLogin={() => setAuthMode('login')}
          />
        )}

        {/* Global Toast Notification */}
        {toast && (
          <div className={`toast ${toast.type}`}>
            {toast.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
            <span>{toast.message}</span>
          </div>
        )}
      </>
    );
  }

  // Authenticated State: Render Main Dashboard Layout
  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab)}
        health={health}
        queueCount={summary?.waiting_queue_count ?? queue.length}
        currentUser={currentUser}
        onLogout={handleLogout}
      />

      <main className="main-area">
        <Header
          activeTab={activeTab}
          health={health}
          onRefresh={loadAllData}
          isLoading={isLoading}
          currentUser={currentUser}
          onLogout={handleLogout}
        />

        {activeTab === 'dashboard' && (
          <DashboardView
            summary={summary}
            activeSessions={activeSessions}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'slots' && (
          <ParkingSlotsView
            slots={slots}
            isLoading={isLoading}
            onRefresh={loadAllData}
            showToast={showToast}
          />
        )}

        {activeTab === 'entry' && (
          <VehicleEntryView
            onSuccess={handleOperationSuccess}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'exit' && (
          <VehicleExitView
            activeSessions={activeSessions}
            onSuccess={handleOperationSuccess}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'reservations' && (
          <ReservationsView
            reservations={reservations}
            availableSlots={slots.filter((s) => s.status === 'available')}
            isLoading={isLoading}
            onRefresh={loadAllData}
            onNavigate={(tab) => setActiveTab(tab)}
            showToast={showToast}
          />
        )}

        {activeTab === 'queue' && (
          <QueueManagementView
            queue={queue}
            isLoading={isLoading}
            onRefresh={loadAllData}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'history' && (
          <ParkingHistoryView
            history={history}
            isLoading={isLoading}
            onRefresh={loadAllData}
          />
        )}
      </main>

      {/* Global Toast Notification */}
      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
};

export default App;
