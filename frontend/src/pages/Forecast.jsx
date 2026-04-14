import React, { useEffect, useState } from 'react';
import { getForecast } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';

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
      
      <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', marginBottom: '30px' }}>
        <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '20px' }}>Predicted vs Actual Demand (Line Chart)</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2} name="Predicted" dot={{ fill: '#3b82f6' }} />
            <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={2} name="Actual" dot={{ fill: '#10b981' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', marginBottom: '30px' }}>
        <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '20px' }}>Demand Comparison (Bar Chart)</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="predicted" fill="#3b82f6" name="Predicted" />
            <Bar dataKey="actual" fill="#10b981" name="Actual" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: 'white', padding: '30px', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '20px' }}>Forecast Details</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'center' }}>
          <thead>
            <tr style={{ backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
              <th style={{ padding: '15px', color: '#475569' }}>Month</th>
              <th style={{ padding: '15px', color: '#475569' }}>Predicted Demand</th>
              <th style={{ padding: '15px', color: '#475569' }}>Actual Demand</th>
              <th style={{ padding: '15px', color: '#475569' }}>Variance</th>
              <th style={{ padding: '15px', color: '#475569' }}>Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {data.map(item => {
              const variance = item.actual - item.predicted;
              const accuracy = ((1 - Math.abs(variance) / item.actual) * 100).toFixed(1);
              return (
                <tr key={item.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '15px', fontWeight: 'bold' }}>{item.month}</td>
                  <td style={{ padding: '15px', color: '#3b82f6' }}>{item.predicted}</td>
                  <td style={{ padding: '15px', color: '#10b981' }}>{item.actual}</td>
                  <td style={{ padding: '15px', color: variance >= 0 ? '#10b981' : '#ef4444' }}>
                    {variance > 0 ? '+' : ''}{variance}
                  </td>
                  <td style={{ padding: '15px', color: '#64748b' }}>{accuracy}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Forecast;
