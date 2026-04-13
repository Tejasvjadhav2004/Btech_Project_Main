import React, { useEffect, useState } from 'react';
import { getWarehouses } from '../services/api';

const Warehouses = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWarehouses()
      .then(res => {
        setWarehouses(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Warehouses</h1>

      <div style={{ backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '20px', color: '#64748b' }}>Loading warehouses...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '15px', color: '#475569' }}>Warehouse ID</th>
                <th style={{ padding: '15px', color: '#475569' }}>Name</th>
                <th style={{ padding: '15px', color: '#475569' }}>Location</th>
                <th style={{ padding: '15px', color: '#475569' }}>Capacity</th>
              </tr>
            </thead>
            <tbody>
              {warehouses.length === 0 ? (
                <tr><td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No warehouses found</td></tr>
              ) : (
                warehouses.map(wh => (
                  <tr key={wh.warehouse_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '15px', fontWeight: 'bold' }}>{wh.warehouse_id}</td>
                    <td style={{ padding: '15px' }}>{wh.name}</td>
                    <td style={{ padding: '15px' }}>
                      {wh.location ? `${wh.location.latitude?.toFixed(2)}, ${wh.location.longitude?.toFixed(2)}` : 'N/A'}
                    </td>
                    <td style={{ padding: '15px' }}>
                      <div style={{ width: '100%', backgroundColor: '#e2e8f0', borderRadius: '4px', height: '10px', overflow: 'hidden', marginTop: '5px' }}>
                        <div style={{ width: `${(wh.current_utilization || 0) / (wh.total_capacity || 1) * 100}%`, backgroundColor: '#3b82f6', height: '100%' }}></div>
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                        {wh.current_utilization || 0} / {wh.total_capacity || 1000} utilized
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Warehouses;
