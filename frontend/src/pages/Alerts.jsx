import React, { useEffect, useState } from 'react';
import { getAlerts } from '../services/api';
import { usePolling } from '../hooks/usePolling';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = () => {
    getAlerts()
      .then(res => {
        setAlerts(res.alerts || []);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  usePolling(() => {
    fetchAlerts();
  }, 5000);

  const getAlertColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return '#dc2626'; // Red
      case 'high': return '#ea580c';     // Orange
      case 'medium': return '#eab308';   // Yellow
      default: return '#3b82f6';         // Blue
    }
  };

  if (loading && alerts.length === 0) return <div>Loading alerts...</div>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ color: '#0f172a', margin: 0 }}>System Alerts</h1>
        <span style={{ backgroundColor: '#e2e8f0', padding: '5px 15px', borderRadius: '20px', fontSize: '14px' }}>
          Auto-refreshing (5s) • {alerts.length} Active
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {alerts.length === 0 ? (
          <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '10px', textAlign: 'center', color: '#64748b' }}>
            No active alerts
          </div>
        ) : (
          alerts.map(alert => (
            <div key={alert.signal_id} style={{ 
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '10px',
              borderLeft: `5px solid ${getAlertColor(alert.severity)}`,
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ 
                    backgroundColor: getAlertColor(alert.severity), 
                    color: 'white', 
                    padding: '3px 8px', 
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    textTransform: 'uppercase'
                  }}>
                    {alert.severity}
                  </span>
                  <h3 style={{ margin: 0, color: '#1e293b' }}>{alert.title}</h3>
                </div>
                <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>{alert.description}</p>
                {alert.entity_id && (
                  <p style={{ margin: '5px 0 0', color: '#94a3b8', fontSize: '12px' }}>Entity ID: {alert.entity_id}</p>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ color: '#94a3b8', fontSize: '12px' }}>
                  {new Date(alert.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Alerts;
