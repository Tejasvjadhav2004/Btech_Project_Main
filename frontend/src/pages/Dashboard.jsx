import React, { useEffect, useState } from 'react';
import { getDashboardOverview } from '../services/api';

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardOverview()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading dashboard...</div>;
  if (!data) return <div>Error loading dashboard data.</div>;

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Dashboard Overview</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
        <Card title="Total Products" value={data.total_products} />
        <Card title="Total Stock" value={data.total_stock} />
        <Card title="Low Stock Alerts" value={data.low_stock_alerts} color={data.low_stock_alerts > 0 ? '#ef4444' : '#22c55e'} />
        <Card title="Warehouse Utilization" value={`${(data.warehouse_utilization || 0).toFixed(1)}%`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155' }}>Recent Activity</h3>
          <p style={{ color: '#64748b' }}>Total Revenue: ${data.total_revenue?.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

const Card = ({ title, value, color }) => (
  <div style={{
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
    borderLeft: color ? `4px solid ${color}` : '4px solid #38bdf8'
  }}>
    <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b', fontWeight: 'normal' }}>{title}</h3>
    <p style={{ margin: '10px 0 0 0', fontSize: '24px', fontWeight: 'bold', color: color || '#0f172a' }}>{value}</p>
  </div>
);

export default Dashboard;
