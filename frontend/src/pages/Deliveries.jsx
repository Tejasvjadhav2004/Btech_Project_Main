import React, { useEffect, useState } from 'react';
import { getDeliveries, startDelivery, completeDelivery } from '../services/api';

const Deliveries = () => {
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('All');
  const [limit, setLimit] = useState(50);

  const fetchDeliveriesList = () => {
    setLoading(true);
    getDeliveries(limit, statusFilter)
      .then(res => {
        setDeliveries(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDeliveriesList();
  }, [limit, statusFilter]);

  const handleAction = async (id, action) => {
    try {
      if (action === 'start') await startDelivery(id);
      else if (action === 'complete') await completeDelivery(id);
      alert(`Delivery ${action}ed successfully!`);
      fetchDeliveriesList();
    } catch (e) {
      alert(`Error: ${e.message}`);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'in_transit': return { bg: '#e0f2fe', text: '#0284c7' };
      case 'delivered': return { bg: '#dcfce3', text: '#166534' };
      case 'failed': return { bg: '#fee2e2', text: '#991b1b' };
      case 'cancelled': return { bg: '#f1f5f9', text: '#475569' };
      default: return { bg: '#fef3c7', text: '#d97706' }; // pending
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ color: '#0f172a', margin: 0 }}>Deliveries</h1>
        <button onClick={fetchDeliveriesList} style={{ padding: '8px 16px', background: 'white', border: '1px solid #cbd5e1', borderRadius: '5px', cursor: 'pointer' }}>
          🔄 Refresh
        </button>
      </div>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', backgroundColor: 'white', padding: '15px', borderRadius: '10px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '14px', color: '#64748b', marginBottom: '5px' }}>Filter Status</label>
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '8px', borderRadius: '5px', border: '1px solid #cbd5e1', width: '150px' }}
          >
            <option value="All">All</option>
            <option value="pending">Pending</option>
            <option value="in_transit">In Transit</option>
            <option value="delivered">Delivered</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <label style={{ fontSize: '14px', color: '#64748b', marginBottom: '5px' }}>Limit Results</label>
          <input 
            type="number" 
            value={limit} 
            onChange={(e) => setLimit(e.target.value)} 
            style={{ padding: '8px', borderRadius: '5px', border: '1px solid #cbd5e1', width: '100px' }}
          />
        </div>
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '20px', color: '#64748b' }}>Loading deliveries...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '15px', color: '#475569' }}>Delivery ID / Order</th>
                <th style={{ padding: '15px', color: '#475569' }}>Route</th>
                <th style={{ padding: '15px', color: '#475569' }}>Transport / ETA</th>
                <th style={{ padding: '15px', color: '#475569' }}>Status</th>
                <th style={{ padding: '15px', color: '#475569' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {deliveries.length === 0 ? (
                <tr><td colSpan="5" style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No deliveries found</td></tr>
              ) : (
                deliveries.map(delivery => {
                  const colors = getStatusColor(delivery.status);
                  return (
                    <tr key={delivery.delivery_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{ padding: '15px' }}>
                        <div style={{ fontWeight: 'bold', color: '#0f172a' }}>{delivery.delivery_id}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>Order: {delivery.order_id}</div>
                      </td>
                      <td style={{ padding: '15px' }}>
                        <div style={{ color: '#334155' }}>📍 {delivery.warehouse_id} → {delivery.store_id}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>{delivery.distance_km?.toFixed(1) || 0} km</div>
                      </td>
                      <td style={{ padding: '15px' }}>
                        <div style={{ color: '#334155', textTransform: 'capitalize' }}>🚛 {delivery.transport_mode || 'truck'}</div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>ETA: {delivery.estimated_duration_hours?.toFixed(1) || 0}h</div>
                      </td>
                      <td style={{ padding: '15px' }}>
                        <span style={{ 
                          padding: '4px 10px', 
                          borderRadius: '20px', 
                          fontSize: '12px', 
                          fontWeight: 'bold',
                          backgroundColor: colors.bg, 
                          color: colors.text,
                          textTransform: 'uppercase'
                        }}>
                          {delivery.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ padding: '15px' }}>
                        {delivery.status === 'pending' && (
                          <button onClick={() => handleAction(delivery.delivery_id, 'start')} style={{ padding: '6px 12px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Start Delivery</button>
                        )}
                        {delivery.status === 'in_transit' && (
                          <button onClick={() => handleAction(delivery.delivery_id, 'complete')} style={{ padding: '6px 12px', background: '#22c55e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Complete Delivery</button>
                        )}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Deliveries;
