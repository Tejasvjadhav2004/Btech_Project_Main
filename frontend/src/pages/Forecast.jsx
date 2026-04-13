import React, { useEffect, useState } from 'react';
import { getForecast } from '../services/api';

const Forecast = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getForecast()
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading forecast...</div>;

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Demand Forecast</h1>
      
      <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
              <th style={{ padding: '15px', color: '#475569' }}>Month</th>
              <th style={{ padding: '15px', color: '#475569' }}>Predicted Demand</th>
              <th style={{ padding: '15px', color: '#475569' }}>Actual Demand</th>
              <th style={{ padding: '15px', color: '#475569' }}>Variance</th>
            </tr>
          </thead>
          <tbody>
            {data.map(item => (
              <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                <td style={{ padding: '15px', fontWeight: 'bold' }}>{item.month}</td>
                <td style={{ padding: '15px', color: '#3b82f6' }}>{item.predicted}</td>
                <td style={{ padding: '15px', color: '#10b981' }}>{item.actual}</td>
                <td style={{ padding: '15px', color: item.actual - item.predicted >= 0 ? '#10b981' : '#ef4444' }}>
                  {item.actual - item.predicted > 0 ? '+' : ''}{item.actual - item.predicted}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div style={{ marginTop: '40px', display: 'flex', gap: '20px', alignItems: 'flex-end', height: '200px', padding: '20px', backgroundColor: 'white', borderRadius: '10px' }}>
        {data.map((item) => {
          const maxVal = Math.max(...data.map(d => Math.max(d.predicted, d.actual)));
          const predHeight = (item.predicted / maxVal) * 100 + '%';
          const actHeight = (item.actual / maxVal) * 100 + '%';
          
          return (
            <div key={item.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end', height: '100%', width: '100%', justifyContent: 'center' }}>
                <div style={{ width: '30%', height: predHeight, backgroundColor: '#3b82f6', borderRadius: '4px 4px 0 0' }} title={`Predicted: ${item.predicted}`}></div>
                <div style={{ width: '30%', height: actHeight, backgroundColor: '#10b981', borderRadius: '4px 4px 0 0' }} title={`Actual: ${item.actual}`}></div>
              </div>
              <span style={{ marginTop: '10px', fontSize: '14px', color: '#64748b' }}>{item.month}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Forecast;
