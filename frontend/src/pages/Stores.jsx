import React, { useEffect, useState } from 'react';
import { getStores } from '../services/api';

const Stores = () => {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStores()
      .then(res => {
        setStores(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Stores</h1>

      <div style={{ backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '20px', color: '#64748b' }}>Loading stores...</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '15px', color: '#475569' }}>Store ID</th>
                <th style={{ padding: '15px', color: '#475569' }}>Name</th>
                <th style={{ padding: '15px', color: '#475569' }}>Location</th>
                <th style={{ padding: '15px', color: '#475569' }}>Capacity</th>
              </tr>
            </thead>
            <tbody>
              {stores.length === 0 ? (
                <tr><td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No stores found</td></tr>
              ) : (
                stores.map(store => (
                  <tr key={store.store_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '15px', fontWeight: 'bold' }}>{store.store_id}</td>
                    <td style={{ padding: '15px' }}>{store.name}</td>
                    <td style={{ padding: '15px' }}>
                      {store.location ? `${store.location.latitude?.toFixed(2)}, ${store.location.longitude?.toFixed(2)}` : 'N/A'}
                    </td>
                    <td style={{ padding: '15px' }}>
                      <div style={{ width: '100%', backgroundColor: '#e2e8f0', borderRadius: '4px', height: '10px', overflow: 'hidden', marginTop: '5px' }}>
                        <div style={{ width: `${(store.current_utilization || 0) / (store.total_capacity || 1) * 100}%`, backgroundColor: '#3b82f6', height: '100%' }}></div>
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                        {store.current_utilization || 0} / {store.total_capacity || 1000} utilized
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

export default Stores;
