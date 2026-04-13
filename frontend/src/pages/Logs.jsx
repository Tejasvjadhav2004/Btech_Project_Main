import React, { useEffect, useState } from 'react';
import { getLogs } from '../services/api';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLogs()
      .then(res => {
        setLogs(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading logs...</div>;

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>System Logs & Anomalies</h1>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {logs.length === 0 ? (
          <div style={{ padding: '20px', backgroundColor: 'white', borderRadius: '10px', textAlign: 'center', color: '#64748b' }}>
            No execution logs found
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.execution_id} style={{ 
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              borderLeft: log.status === 'failed' ? '4px solid #ef4444' : log.status === 'completed' ? '4px solid #22c55e' : '4px solid #eab308'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <strong style={{ color: '#334155' }}>Execution: {log.execution_id}</strong>
                <span style={{ 
                  color: log.status === 'failed' ? '#ef4444' : log.status === 'completed' ? '#22c55e' : '#eab308',
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                  fontSize: '12px'
                }}>
                  {log.status}
                </span>
              </div>
              <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '10px' }}>
                Order ID: {log.order_id} | {new Date(log.started_at).toLocaleString()}
              </div>

              {log.status === 'failed' && log.error && (
                <div style={{ backgroundColor: '#fef2f2', padding: '10px', borderRadius: '5px', marginTop: '10px', color: '#991b1b', fontSize: '14px' }}>
                  <strong>Anomaly / Error: </strong> {log.error.message || 'Unknown error occurred'}
                </div>
              )}

              {log.steps && log.steps.length > 0 && (
                <div style={{ marginTop: '10px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
                  <p style={{ fontSize: '13px', fontWeight: 'bold', color: '#475569', marginBottom: '5px' }}>Execution Steps:</p>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#64748b' }}>
                    {log.steps.map(step => (
                      <li key={step.step_id} style={{ marginBottom: '4px' }}>
                        {step.step}: {step.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Logs;
