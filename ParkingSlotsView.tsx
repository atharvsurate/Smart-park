import React, { useState } from 'react';
import {
  Plus,
  Zap,
  Accessibility,
  Car,
  Minimize2,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import type { ParkingSlot, SlotType, SlotStatus } from '../types';
import { createParkingSlot, seedParkingSlots } from '../api/client';

interface ParkingSlotsViewProps {
  slots: ParkingSlot[];
  isLoading: boolean;
  onRefresh: () => void;
  showToast: (msg: string, type: 'success' | 'error') => void;
}

export const ParkingSlotsView: React.FC<ParkingSlotsViewProps> = ({
  slots,
  isLoading,
  onRefresh,
  showToast,
}) => {
  const [floorFilter, setFloorFilter] = useState<number | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<SlotStatus | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<SlotType | 'all'>('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newSlotNumber, setNewSlotNumber] = useState('');
  const [newSlotType, setNewSlotType] = useState<SlotType>('standard');
  const [newSlotFloor, setNewSlotFloor] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  // Filter logic
  const filteredSlots = slots.filter((slot) => {
    if (floorFilter !== 'all' && slot.floor !== floorFilter) return false;
    if (statusFilter !== 'all' && slot.status !== statusFilter) return false;
    if (typeFilter !== 'all' && slot.slot_type !== typeFilter) return false;
    return true;
  });

  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!newSlotNumber.trim()) {
      setFormError('Please enter a valid slot number (e.g. C-301).');
      return;
    }

    try {
      setIsSubmitting(true);
      await createParkingSlot({
        slot_number: newSlotNumber.trim().toUpperCase(),
        slot_type: newSlotType,
        floor: Number(newSlotFloor),
      });
      showToast(`Slot ${newSlotNumber.toUpperCase()} created successfully!`, 'success');
      setIsModalOpen(false);
      setNewSlotNumber('');
      onRefresh();
    } catch (err: any) {
      setFormError(err.message || 'Failed to create slot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSeed = async () => {
    try {
      const res = await seedParkingSlots();
      showToast(res.message, 'success');
      onRefresh();
    } catch (err: any) {
      showToast(err.message || 'Failed to seed slots.', 'error');
    }
  };

  const getSlotTypeIcon = (type: SlotType) => {
    switch (type) {
      case 'ev':
        return <Zap size={14} style={{ color: 'var(--accent-ev)' }} />;
      case 'accessible':
        return <Accessibility size={14} style={{ color: '#a78bfa' }} />;
      case 'compact':
        return <Minimize2 size={14} style={{ color: '#38bdf8' }} />;
      default:
        return <Car size={14} style={{ color: '#94a3b8' }} />;
    }
  };

  return (
    <div className="page-content">
      {/* Toolbar / Filters */}
      <div className="slots-toolbar">
        <div className="filter-group">
          <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600 }}>Floor:</span>
          {(['all', 1, 2] as const).map((f) => (
            <button
              key={f}
              className={`filter-btn ${floorFilter === f ? 'active' : ''}`}
              onClick={() => setFloorFilter(f)}
            >
              {f === 'all' ? 'All Floors' : `Floor ${f}`}
            </button>
          ))}

          <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600, marginLeft: '12px' }}>
            Status:
          </span>
          {(['all', 'available', 'occupied', 'reserved'] as const).map((s) => (
            <button
              key={s}
              className={`filter-btn ${statusFilter === s ? 'active' : ''}`}
              onClick={() => setStatusFilter(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}

          <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: 600, marginLeft: '12px' }}>
            Type:
          </span>
          {(['all', 'standard', 'ev', 'compact', 'accessible'] as const).map((t) => (
            <button
              key={t}
              className={`filter-btn ${typeFilter === t ? 'active' : ''}`}
              onClick={() => setTypeFilter(t)}
            >
              {t.toUpperCase()}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {slots.length === 0 && (
            <button className="btn-secondary" onClick={handleSeed}>
              <Sparkles size={14} />
              <span>Seed 20 Default Slots</span>
            </button>
          )}

          <button
            id="btn-add-slot-modal"
            className="btn-primary"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={15} />
            <span>Add Slot</span>
          </button>
        </div>
      </div>

      {/* Slots Summary Pill */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Showing <strong>{filteredSlots.length}</strong> of <strong>{slots.length}</strong> total slots
        </p>
        {isLoading && (
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={12} className="spin-icon" /> Synchronizing SQLite records...
          </span>
        )}
      </div>

      {/* Slots Grid */}
      <div className="slots-grid">
        {filteredSlots.map((slot) => (
          <div key={slot.id} className={`slot-card status-${slot.status}`}>
            <div className="slot-header">
              <div>
                <span className="slot-number">{slot.slot_number}</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                  ID: #{slot.id}
                </span>
              </div>
              <span className={`slot-badge ${slot.status}`}>
                {slot.status}
              </span>
            </div>

            <div className="slot-details">
              <div className="detail-row">
                <span>Category</span>
                <span className="detail-val" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {getSlotTypeIcon(slot.slot_type)}
                  <span style={{ textTransform: 'capitalize' }}>{slot.slot_type}</span>
                </span>
              </div>

              <div className="detail-row">
                <span>Floor Level</span>
                <span className="detail-val">Floor {slot.floor}</span>
              </div>

              {slot.current_vehicle_plate && (
                <div style={{ marginTop: '6px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '3px' }}>
                    Occupying Vehicle
                  </div>
                  <div className="plate-badge">
                    {slot.current_vehicle_plate}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {filteredSlots.length === 0 && !isLoading && (
          <div style={{ gridColumn: '1 / -1', padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No parking slots found matching the selected filters.
          </div>
        )}
      </div>

      {/* Add Slot Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => setIsModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#ffffff' }}>Add Parking Slot</h3>
              <button
                className="btn-secondary"
                style={{ padding: '4px 8px', fontSize: '12px' }}
                onClick={() => setIsModalOpen(false)}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSlot} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Slot Identifier</label>
                <input
                  type="text"
                  placeholder="e.g. A-111, B-211"
                  className="form-input"
                  value={newSlotNumber}
                  onChange={(e) => setNewSlotNumber(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Floor</label>
                <select
                  className="form-select"
                  value={newSlotFloor}
                  onChange={(e) => setNewSlotFloor(Number(e.target.value))}
                >
                  <option value={1}>Floor 1</option>
                  <option value={2}>Floor 2</option>
                  <option value={3}>Floor 3</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Slot Category</label>
                <select
                  className="form-select"
                  value={newSlotType}
                  onChange={(e) => setNewSlotType(e.target.value as SlotType)}
                >
                  <option value="standard">Standard (Sedan/Hatchback)</option>
                  <option value="compact">Compact (Bikes/Small Cars)</option>
                  <option value="ev">EV Charging Bay</option>
                  <option value="accessible">Accessible / Reserved Bay</option>
                </select>
              </div>

              {formError && <div className="form-error">{formError}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Adding...' : 'Create Slot'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
