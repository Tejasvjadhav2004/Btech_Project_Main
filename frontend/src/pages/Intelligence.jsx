import React, { useEffect, useState } from 'react';
import { 
  getSignalStats, 
  getSchedulerStatus, 
  getActiveSignals, 
  runDetection, 
  runAllDetections, 
  startScheduler, 
  stopScheduler, 
  acknowledgeSignal, 
  resolveSignal,
  getReplenishmentOrders,
  approveReplenishmentOrder
} from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Intelligence = () => {
  const [stats, setStats] = useState(null);
  const [scheduler, setScheduler] = useState(null);
  const [activeSignals, setActiveSignals] = useState([]);
  const [replenishmentOrders, setReplenishmentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, schedulerData, signalsData, replenishmentData] = await Promise.all([
        getSignalStats(),
        getSchedulerStatus(),
        getActiveSignals(),
        getReplenishmentOrders().catch(() => ({ orders: [] })) // Handle replenishment orders gracefully
      ]);
      setStats(statsData);
      setScheduler(schedulerData);
      setActiveSignals(signalsData?.signals || []);
      setReplenishmentOrders(replenishmentData?.orders || []);
    } catch (e) {
      console.error("Error fetching intelligence data:", e);
      // Set fallback data to prevent empty displays
      setStats(statsData || { active_signals: 0, total_signals: 0 });
      setScheduler(schedulerData || { is_running: false, job_count: 0 });
      setActiveSignals([]);
      setReplenishmentOrders([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDetection = async (type) => {
    try {
      await runDetection(type);
      alert(`Detection ${type} triggered successfully`);
      fetchData();
    } catch (e) {
      alert(`Error running detection: ${e.message}`);
    }
  };

  const getSignalTypeLabel = (type) => {
    const labels = {
      'LOW_STOCK': 'Low Stock',
      'STOCKOUT': 'Stockout',
      'DELIVERY_DELAY': 'Delivery Delay',
      'DEMAND_SPIKE': 'Demand Spike',
      'DEMAND_DROP': 'Demand Drop',
      'OVERSTOCK': 'Overstock',
      'OVER_UTILIZATION': 'Over Utilization',
      'UNDER_UTILIZATION': 'Under Utilization'
    };
    return labels[type] || type;
  };

  const handleRunAll = async () => {
    try {
      await runAllDetections();
      alert('All detections triggered successfully');
      fetchData();
    } catch (e) {
      alert(`Error running all detections: ${e.message}`);
    }
  };

  const handleScheduler = async (action) => {
    try {
      if (action === 'start') await startScheduler();
      else await stopScheduler();
      fetchData();
    } catch (e) {
      alert(`Error ${action}ing scheduler: ${e.message}`);
    }
  };

  const handleSignalAction = async (id, action) => {
    try {
      if (action === 'ack') await acknowledgeSignal(id);
      else await resolveSignal(id);
      fetchData();
    } catch (e) {
      alert(`Error: ${e.message}`);
    }
  };

  const handleApproveOrder = async (id) => {
    try {
      await approveReplenishmentOrder(id);
      alert('Replenishment Order Approved!');
      fetchData();
    } catch (e) {
      alert(`Error approving order: ${e.message}`);
    }
  };

  const severityColor = (severity) => {
    switch(severity?.toLowerCase()) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      default: return '#22c55e';
    }
  };

  // Prepare data for charts
  const severityData = [
    { name: 'Critical', value: activeSignals.filter(s => s.severity === 'critical').length, color: '#ef4444' },
    { name: 'High', value: activeSignals.filter(s => s.severity === 'high').length, color: '#f97316' },
    { name: 'Medium', value: activeSignals.filter(s => s.severity === 'medium').length, color: '#eab308' },
    { name: 'Low', value: activeSignals.filter(s => s.severity === 'low').length, color: '#22c55e' }
  ].filter(d => d.value > 0);

  const signalTypeData = [
    { name: 'Low Stock', value: activeSignals.filter(s => s.type === 'LOW_STOCK').length },
    { name: 'Stockout', value: activeSignals.filter(s => s.type === 'STOCKOUT').length },
    { name: 'Delivery Delay', value: activeSignals.filter(s => s.type === 'DELIVERY_DELAY').length },
    { name: 'Demand Spike', value: activeSignals.filter(s => s.type === 'DEMAND_SPIKE').length },
    { name: 'Demand Drop', value: activeSignals.filter(s => s.type === 'DEMAND_DROP').length },
    { name: 'Overstock', value: activeSignals.filter(s => s.type === 'OVERSTOCK').length },
    { name: 'Over Utilization', value: activeSignals.filter(s => s.type === 'OVER_UTILIZATION').length },
    { name: 'Under Utilization', value: activeSignals.filter(s => s.type === 'UNDER_UTILIZATION').length }
  ].filter(d => d.value > 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1 style={{ color: '#0f172a', margin: 0 }}>Intelligence Panel</h1>
        <button onClick={fetchData} style={{ padding: '8px 16px', backgroundColor: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '5px', cursor: 'pointer' }}>
          🔄 Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Active Signals</h3>
          <p style={{ margin: '10px 0 0 0', fontSize: '24px', fontWeight: 'bold' }}>{stats?.active_signals || 0}</p>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Total Signals</h3>
          <p style={{ margin: '10px 0 0 0', fontSize: '24px', fontWeight: 'bold' }}>{stats?.total_signals || 0}</p>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Scheduler Status</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px' }}>
            <span style={{ fontSize: '18px', fontWeight: 'bold', color: scheduler?.is_running ? '#22c55e' : '#ef4444' }}>
              {scheduler?.is_running ? '🟢 Running' : '🔴 Stopped'}
            </span>
            {scheduler?.is_running ? (
              <button onClick={() => handleScheduler('stop')} style={{ padding: '4px 8px', fontSize: '12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>Stop</button>
            ) : (
              <button onClick={() => handleScheduler('start')} style={{ padding: '4px 8px', fontSize: '12px', background: '#22c55e', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer' }}>Start</button>
            )}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Scheduler Jobs</h3>
          <p style={{ margin: '10px 0 0 0', fontSize: '24px', fontWeight: 'bold' }}>{scheduler?.job_count || 0}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155' }}>Signal Analytics</h3>
          
          {activeSignals.length > 0 && (
            <>
              <div style={{ marginBottom: '30px' }}>
                <h4 style={{ color: '#64748b', marginBottom: '15px' }}>Signals by Severity</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={severityData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div style={{ marginBottom: '30px' }}>
                <h4 style={{ color: '#64748b', marginBottom: '15px' }}>Signals by Type</h4>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={signalTypeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Active Signals</h3>
          {activeSignals.length === 0 ? (
            <p style={{ color: '#64748b' }}>No active signals detected.</p>
          ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {activeSignals.map(sig => (
                  <div key={sig.signal_id} style={{ borderLeft: `4px solid ${severityColor(sig.severity)}`, padding: '15px', backgroundColor: '#f8fafc', borderRadius: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <div>
                        <strong style={{ fontSize: '16px' }}>{getSignalTypeLabel(sig.type)}</strong>
                        <span style={{ marginLeft: '10px', fontSize: '12px', padding: '2px 6px', background: severityColor(sig.severity), color: 'white', borderRadius: '10px' }}>{sig.severity}</span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button onClick={() => handleSignalAction(sig.signal_id, 'ack')} style={{ padding: '4px 10px', background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Acknowledge</button>
                        <button onClick={() => handleSignalAction(sig.signal_id, 'resolve')} style={{ padding: '4px 10px', background: '#22c55e', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>Resolve</button>
                      </div>
                    </div>
                    <p style={{ margin: 0, fontSize: '14px', color: '#475569' }}>{sig.message}</p>
                    {sig.entity_id && <p style={{ margin: '5px 0 0', fontSize: '12px', color: '#94a3b8' }}>Entity: {sig.entity_id}</p>}
                  </div>
                ))}
              </div>
          )}
        </div>

        <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155' }}>Manual Controls</h3>
          <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>Trigger manual detections to sync intelligence data.</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button onClick={() => handleDetection('low-stock')} style={controlBtnStyle}>🔍 Detect Low Stock</button>
            <button onClick={() => handleDetection('stockout')} style={controlBtnStyle}>🚨 Detect Stockout</button>
            <button onClick={() => handleDetection('delivery-delay')} style={controlBtnStyle}>🚚 Detect Delivery Delays</button>
            <button onClick={() => handleDetection('demand-spike')} style={controlBtnStyle}>📈 Detect Demand Spike</button>
            <button onClick={() => handleDetection('utilization')} style={controlBtnStyle}>🏭 Detect Utilization</button>
            <hr style={{ width: '100%', borderColor: '#f1f5f9' }} />
            <button onClick={handleRunAll} style={{ ...controlBtnStyle, background: '#0f172a', color: 'white', border: 'none' }}>🔄 Run All Detections</button>
          </div>
          
          <h3 style={{ marginTop: '30px', color: '#334155' }}>Pending Replenishment</h3>
          {replenishmentOrders.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '14px' }}>No pending orders.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {replenishmentOrders.map(order => (
                <div key={order.order_id} style={{ padding: '10px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                    <strong>{order.order_id}</strong>
                    <button onClick={() => handleApproveOrder(order.order_id)} style={{ padding: '2px 8px', background: '#22c55e', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', fontSize: '12px' }}>Approve</button>
                  </div>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>SKU: {order.items?.[0]?.sku} (Qty: {order.items?.[0]?.quantity})</p>
                  <p style={{ margin: 0, fontSize: '12px', color: '#64748b' }}>Warehouse: {order.warehouse_id}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const controlBtnStyle = {
  padding: '12px',
  textAlign: 'left',
  background: '#f8fafc',
  border: '1px solid #e2e8f0',
  borderRadius: '6px',
  cursor: 'pointer',
  fontWeight: '500',
  color: '#334155',
  transition: 'background 0.2s'
};

export default Intelligence;
