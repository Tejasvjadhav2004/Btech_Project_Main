import React, { useState, useEffect } from 'react';
import { 
  getDeliveries,
  startDelivery,
  completeDelivery,
  getActiveSignals
} from '../../services/api';
import { Truck, Package, Hourglass, AlertTriangle, CheckCircle2, Siren, ClipboardList } from 'lucide-react';
import './LogisticsManagerDashboard.css';

function LogisticsManagerDashboard({ userRole }) {
  const [deliveries, setDeliveries] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState('All');

  useEffect(() => {
    loadLogisticsData();
  }, [selectedStatus, userRole]); // Add userRole to dependencies to re-fetch when role changes

  const loadLogisticsData = async () => {
    try {
      setLoading(true);
      const [deliveriesData, signalsData] = await Promise.all([
        getDeliveries(100, selectedStatus),
        getActiveSignals()
      ]);

      setDeliveries(deliveriesData.deliveries || []);
      setSignals(signalsData.signals || []);
    } catch (error) {
      console.error('Error loading logistics dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartDelivery = async (deliveryId) => {
    try {
      await startDelivery(deliveryId);
      loadLogisticsData();
    } catch (error) {
      console.error('Error starting delivery:', error);
      alert('Failed to start delivery');
    }
  };

  const handleCompleteDelivery = async (deliveryId) => {
    try {
      await completeDelivery(deliveryId);
      loadLogisticsData();
    } catch (error) {
      console.error('Error completing delivery:', error);
      alert('Failed to complete delivery');
    }
  };

  const delayedDeliveries = deliveries.filter(d => 
    d.status === 'IN_TRANSIT' && 
    new Date(d.estimated_delivery) < new Date()
  );

  const deliveryDelaySignals = signals.filter(s => 
    s.type === 'DELIVERY_DELAY'
  );

  if (loading) {
    return (
      <div className="logistics-manager-dashboard">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading logistics operations dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="logistics-manager-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1><Truck size={28} strokeWidth={1.8} style={{ verticalAlign: 'middle', marginRight: '10px' }} />Logistics Manager Dashboard</h1>
          <p className="subtitle">Track deliveries and manage logistics operations</p>
        </div>
        <div className="header-actions">
          <select 
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="status-filter"
          >
            <option value="All">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="IN_TRANSIT">In Transit</option>
            <option value="DELIVERED">Delivered</option>
            <option value="DELAYED">Delayed</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card primary">
          <div className="kpi-icon"><Package size={24} /></div>
          <div className="kpi-content">
            <h3>Total Deliveries</h3>
            <p className="kpi-value">{deliveries.length}</p>
            <p className="kpi-trend">All time</p>
          </div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-icon"><Hourglass size={24} /></div>
          <div className="kpi-content">
            <h3>In Transit</h3>
            <p className="kpi-value">
              {deliveries.filter(d => d.status === 'IN_TRANSIT').length}
            </p>
            <p className="kpi-trend">On the way</p>
          </div>
        </div>

        <div className="kpi-card danger">
          <div className="kpi-icon"><AlertTriangle size={24} /></div>
          <div className="kpi-content">
            <h3>Delayed Deliveries</h3>
            <p className="kpi-value">{delayedDeliveries.length}</p>
            <p className="kpi-trend negative">Action needed</p>
          </div>
        </div>

        <div className="kpi-card success">
          <div className="kpi-icon"><CheckCircle2 size={24} /></div>
          <div className="kpi-content">
            <h3>Delivered</h3>
            <p className="kpi-value">
              {deliveries.filter(d => d.status === 'DELIVERED').length}
            </p>
            <p className="kpi-trend positive">Completed</p>
          </div>
        </div>
      </div>

      {/* Delivery Delay Alerts */}
      {delayedDeliveries.length > 0 && (
        <div className="delay-alerts-section">
          <div className="section-header">
            <h3><AlertTriangle size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Delayed Deliveries</h3>
            <span className="badge danger">{delayedDeliveries.length} delayed</span>
          </div>
          <div className="delayed-deliveries-grid">
            {delayedDeliveries.slice(0, 6).map((delivery) => (
              <div key={delivery.delivery_id} className="delayed-delivery-card">
                <div className="delivery-header">
                  <span className="delivery-id">{delivery.delivery_id}</span>
                  <span className="delay-badge">DELAYED</span>
                </div>
                <div className="delivery-details">
                  <p><strong>Order:</strong> {delivery.order_id}</p>
                  <p><strong>Destination:</strong> {delivery.destination}</p>
                  <p><strong>Estimated:</strong> {new Date(delivery.estimated_delivery).toLocaleDateString()}</p>
                  <p><strong>Days Late:</strong> {Math.ceil((new Date() - new Date(delivery.estimated_delivery)) / (1000 * 60 * 60 * 24))}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Delivery Delay Signals */}
      {deliveryDelaySignals.length > 0 && (
        <div className="signals-section">
          <div className="section-header">
            <h3><Siren size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Delivery Delay Signals</h3>
            <span className="badge">{deliveryDelaySignals.length} active</span>
          </div>
          <div className="signals-grid">
            {deliveryDelaySignals.slice(0, 6).map((signal) => (
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
                <div className="signal-footer">
                  <span className="signal-entity">{signal.entity_id}</span>
                  <span className="signal-time">
                    {new Date(signal.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deliveries Table */}
      <div className="deliveries-section">
        <div className="section-header">
          <h3><ClipboardList size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Deliveries</h3>
          <span className="badge">{deliveries.length} total</span>
        </div>
        <div className="deliveries-table">
          <table>
            <thead>
              <tr>
                <th>Delivery ID</th>
                <th>Order ID</th>
                <th>Destination</th>
                <th>Status</th>
                <th>Estimated</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {deliveries.slice(0, 20).map((delivery) => (
                <tr key={delivery.delivery_id}>
                  <td className="delivery-id-cell">{delivery.delivery_id}</td>
                  <td>{delivery.order_id}</td>
                  <td>{delivery.destination}</td>
                  <td>
                    <span className={`status-badge ${delivery.status.toLowerCase()}`}>
                      {delivery.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    {delivery.estimated_delivery 
                      ? new Date(delivery.estimated_delivery).toLocaleDateString()
                      : 'N/A'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      {delivery.status === 'PENDING' && (
                        <button 
                          className="action-button start"
                          onClick={() => handleStartDelivery(delivery.delivery_id)}
                        >
                          Start
                        </button>
                      )}
                      {delivery.status === 'IN_TRANSIT' && (
                        <button 
                          className="action-button complete"
                          onClick={() => handleCompleteDelivery(delivery.delivery_id)}
                        >
                          Complete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default LogisticsManagerDashboard;
