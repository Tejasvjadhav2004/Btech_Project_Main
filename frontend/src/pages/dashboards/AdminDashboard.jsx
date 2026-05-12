import React, { useState, useEffect } from 'react';
import { 
  getSignalStats,
  getActiveSignals,
  getSchedulerStatus,
  runAllDetections,
  startScheduler,
  stopScheduler
} from '../../services/api';
import { Settings, Search, BarChart3, TrendingUp, RefreshCw, Zap, Clock, Play, Square, Radar, ClipboardList, AlertTriangle } from 'lucide-react';
import './AdminDashboard.css';

function AdminDashboard({ userRole }) {
  const [signalStats, setSignalStats] = useState(null);
  const [activeSignals, setActiveSignals] = useState([]);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [runningDetections, setRunningDetections] = useState(false);

  useEffect(() => {
    loadAdminData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadAdminData, 30000);
    return () => clearInterval(interval);
  }, [userRole]); // Add userRole to dependencies to re-fetch when role changes

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const [stats, signals, scheduler] = await Promise.all([
        getSignalStats(),
        getActiveSignals(),
        getSchedulerStatus()
      ]);

      setSignalStats(stats);
      setActiveSignals(signals.signals || []);
      setSchedulerStatus(scheduler);
    } catch (error) {
      console.error('Error loading admin dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAllDetections = async () => {
    try {
      setRunningDetections(true);
      await runAllDetections();
      await loadAdminData();
    } catch (error) {
      console.error('Error running detections:', error);
      alert('Failed to run detections');
    } finally {
      setRunningDetections(false);
    }
  };

  const handleStartScheduler = async () => {
    try {
      await startScheduler();
      await loadAdminData();
    } catch (error) {
      console.error('Error starting scheduler:', error);
      alert('Failed to start scheduler');
    }
  };

  const handleStopScheduler = async () => {
    try {
      await stopScheduler();
      await loadAdminData();
    } catch (error) {
      console.error('Error stopping scheduler:', error);
      alert('Failed to stop scheduler');
    }
  };

  if (loading) {
    return (
      <div className="admin-dashboard">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1><Settings size={28} strokeWidth={1.8} style={{ verticalAlign: 'middle', marginRight: '10px' }} />Admin Dashboard</h1>
          <p className="subtitle">System monitoring, configuration, and controls</p>
        </div>
        <div className="header-actions">
          <button 
            className="run-detections-button"
            onClick={handleRunAllDetections}
            disabled={runningDetections}
          >
            {runningDetections ? 'Running...' : <><Search size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />Run All Detections</>}
          </button>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="status-cards-grid">
        <div className="status-card primary">
          <div className="card-icon"><BarChart3 size={24} /></div>
          <div className="card-content">
            <h3>System Status</h3>
            <p className="status-value">Operational</p>
            <p className="status-trend">All systems normal</p>
          </div>
        </div>

        <div className="status-card success">
          <div className="card-icon"><TrendingUp size={24} /></div>
          <div className="card-content">
            <h3>Active Signals</h3>
            <p className="status-value">{activeSignals.length}</p>
            <p className="status-trend">Requiring attention</p>
          </div>
        </div>

        <div className="status-card warning">
          <div className="card-icon"><RefreshCw size={24} /></div>
          <div className="card-content">
            <h3>Scheduler Status</h3>
            <p className="status-value">
              {schedulerStatus?.status === 'running' ? 'Running' : 'Stopped'}
            </p>
            <p className="status-trend">
              {schedulerStatus?.status === 'running' 
                ? `Next run: ${schedulerStatus?.next_run || 'N/A'}`
                : 'Scheduler not active'}
            </p>
          </div>
        </div>

        <div className="status-card info">
          <div className="card-icon"><Zap size={24} /></div>
          <div className="card-content">
            <h3>Events Processed</h3>
            <p className="status-value">{signalStats?.total_processed || 0}</p>
            <p className="status-trend">Total events logged</p>
          </div>
        </div>
      </div>

      {/* Scheduler Controls */}
      <div className="scheduler-section">
        <div className="section-header">
          <h3><Clock size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Scheduler Controls</h3>
          <span className={`badge ${schedulerStatus?.status === 'running' ? 'success' : 'warning'}`}>
            {schedulerStatus?.status === 'running' ? 'Active' : 'Inactive'}
          </span>
        </div>
        <div className="scheduler-controls">
          <div className="scheduler-info">
            <h4>Current Configuration</h4>
            <div className="scheduler-details">
              <div className="detail-item">
                <span className="label">Status:</span>
                <span className={`value ${schedulerStatus?.status === 'running' ? 'success' : 'warning'}`}>
                  {schedulerStatus?.status === 'running' ? 'Running' : 'Stopped'}
                </span>
              </div>
              <div className="detail-item">
                <span className="label">Intervals:</span>
                <span className="value">Every 5 minutes</span>
              </div>
              <div className="detail-item">
                <span className="label">Detection Functions:</span>
                <span className="value">4 active</span>
              </div>
              {schedulerStatus?.status === 'running' && (
                <div className="detail-item">
                  <span className="label">Next Run:</span>
                  <span className="value">{schedulerStatus?.next_run || 'Calculating...'}</span>
                </div>
              )}
            </div>
          </div>
          <div className="scheduler-actions">
            <h4>Actions</h4>
            <div className="action-buttons">
              <button 
                className="action-button start"
                onClick={handleStartScheduler}
                disabled={schedulerStatus?.status === 'running'}
              >
                <Play size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Start Scheduler
              </button>
              <button 
                className="action-button stop"
                onClick={handleStopScheduler}
                disabled={schedulerStatus?.status !== 'running'}
              >
                <Square size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Stop Scheduler
              </button>
              <button 
                className="action-button detect"
                onClick={handleRunAllDetections}
                disabled={runningDetections}
              >
                <Radar size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Run Detections Now
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Signal Statistics */}
      <div className="signal-stats-section">
        <div className="section-header">
          <h3><BarChart3 size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Signal Statistics</h3>
        </div>
        <div className="stats-grid">
          <div className="stat-card">
            <h4>Total Signals</h4>
            <p className="stat-value">{signalStats?.total_signals || 0}</p>
            <p className="stat-label">All time</p>
          </div>
          <div className="stat-card">
            <h4>Active Signals</h4>
            <p className="stat-value active">{activeSignals.length}</p>
            <p className="stat-label">Currently active</p>
          </div>
          <div className="stat-card">
            <h4>Resolved Signals</h4>
            <p className="stat-value resolved">{signalStats?.resolved_count || 0}</p>
            <p className="stat-label">Successfully resolved</p>
          </div>
          <div className="stat-card">
            <h4>Detection Rate</h4>
            <p className="stat-value">
              {signalStats?.detection_rate ? `${signalStats.detection_rate.toFixed(1)}%` : 'N/A'}
            </p>
            <p className="stat-label">Signal detection</p>
          </div>
        </div>
      </div>

      {/* Signal Distribution by Type */}
      {signalStats?.by_type && (
        <div className="signal-distribution-section">
          <div className="section-header">
            <h3><ClipboardList size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Signal Distribution by Type</h3>
          </div>
          <div className="distribution-grid">
            {Object.entries(signalStats.by_type).map(([type, count]) => (
              <div key={type} className="distribution-card">
                <div className="distribution-header">
                  <span className="signal-type">{type.replace('_', ' ')}</span>
                  <span className="signal-count">{count}</span>
                </div>
                <div className="distribution-bar">
                  <div 
                    className="bar-fill" 
                    style={{ width: `${Math.min((count / (signalStats.total_signals || 1)) * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Signals */}
      {activeSignals.length > 0 && (
        <div className="active-signals-section">
          <div className="section-header">
            <h3><AlertTriangle size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Active Signals Requiring Attention</h3>
            <span className="badge">{activeSignals.length} active</span>
          </div>
          <div className="signals-grid">
            {activeSignals.map((signal) => (
              <div key={signal.signal_id} className="signal-card">
                <div className="signal-header">
                  <span className={`signal-type ${signal.type.toLowerCase()}`}>
                    {signal.type.replace('_', ' ')}
                  </span>
                  <span className={`signal-severity ${signal.severity.toLowerCase()}`}>
                    {signal.severity}
                  </span>
                </div>
                <p className="signal-message">{signal.message}</p>
                <div className="signal-details">
                  <div className="detail-row">
                    <span className="detail-label">Entity:</span>
                    <span className="detail-value">{signal.entity_id}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Product:</span>
                    <span className="detail-value">{signal.product_id || 'N/A'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Created:</span>
                    <span className="detail-value">
                      {new Date(signal.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div className="signal-footer">
                  <span className={`signal-status ${signal.status.toLowerCase()}`}>
                    {signal.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
