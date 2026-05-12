import React, { useEffect, useState } from 'react';
import {
  Activity, AlertTriangle, CheckCircle, Clock, XCircle, Loader, Play, Pause,
  ChevronDown, ChevronUp, RefreshCw, Check, X, Zap, BarChart3
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';

const COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  executing: '#3b82f6',
  monitoring: '#8b5cf6',
  completed: '#10b981',
  failed: '#ef4444',
  waiting_approval: '#f59e0b'
};

const API_BASE = 'http://localhost:8000/api/orchestration';

const Orchestration = () => {
  const [loading, setLoading] = useState(true);
  const [workflows, setWorkflows] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [activeTab, setActiveTab] = useState('active');
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(loadAllData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [workflowsRes, approvalsRes, metricsRes, healthRes] = await Promise.all([
        fetch(`${API_BASE}/active`).then(r => r.json()).catch(() => ({ workflows: [] })),
        fetch(`${API_BASE}/approvals`).then(r => r.json()).catch(() => ({ approvals: [] })),
        fetch(`${API_BASE}/metrics`).then(r => r.json()).catch(() => ({ metrics: {} })),
        fetch(`${API_BASE}/health`).then(r => r.json()).catch(() => ({ status: 'unknown' }))
      ]);

      setWorkflows(workflowsRes.workflows || []);
      setApprovals(approvalsRes.approvals || []);
      setMetrics(metricsRes.metrics || {});
      setHealth(healthRes);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load orchestration data');
    }
    setLoading(false);
  };

  const handleApprove = async (workflowId, approvedBy = 'admin') => {
    try {
      const response = await fetch(`${API_BASE}/approve?workflow_id=${workflowId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved_by: approvedBy, notes: 'Approved via dashboard' })
      });

      if (response.ok) {
        alert(`✓ Workflow ${workflowId} approved and executing!`);
        loadAllData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert(`Error approving workflow: ${err.message}`);
    }
  };

  const handleReject = async (workflowId, reason, rejectedBy = 'admin') => {
    try {
      const response = await fetch(`${API_BASE}/reject?workflow_id=${workflowId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rejected_by: rejectedBy, reason })
      });

      if (response.ok) {
        alert(`✓ Workflow ${workflowId} rejected`);
        loadAllData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert(`Error rejecting workflow: ${err.message}`);
    }
  };

  const handleTriggerOrchestration = async (signalType, severity) => {
    try {
      const response = await fetch(`${API_BASE}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          signal_id: `manual-${Date.now()}`,
          signal_type: signalType,
          severity: severity,
          entity_type: 'manual',
          entity_id: 'test',
          details: { triggered_by: 'dashboard' }
        })
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✓ Orchestration triggered! Workflow: ${result.workflow_id}`);
        loadAllData();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (err) {
      alert(`Error triggering orchestration: ${err.message}`);
    }
  };

  const getStatusColor = (status) => {
    return COLORS[status] || '#6b7280';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'executing':
        return <Loader className="animate-spin" size={16} />;
      case 'monitoring':
        return <Activity size={16} />;
      case 'completed':
        return <CheckCircle size={16} />;
      case 'failed':
        return <XCircle size={16} />;
      case 'waiting_approval':
        return <Clock size={16} />;
      default:
        return <Clock size={16} />;
    }
  };

  // Chart data preparation
  const statusDistribution = [
    { name: 'Executing', value: workflows.filter(w => w.status === 'executing').length },
    { name: 'Monitoring', value: workflows.filter(w => w.status === 'monitoring').length },
    { name: 'Waiting', value: workflows.filter(w => w.status === 'waiting_approval').length },
    { name: 'Completed', value: workflows.filter(w => w.status === 'completed').length }
  ].filter(d => d.value > 0);

  const priorityDistribution = [
    { name: 'Critical', count: workflows.filter(w => w.priority === 'critical').length },
    { name: 'High', count: workflows.filter(w => w.priority === 'high').length },
    { name: 'Medium', count: workflows.filter(w => w.priority === 'medium').length },
    { name: 'Low', count: workflows.filter(w => w.priority === 'low').length }
  ];

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <Loader className="animate-spin" size={48} style={{ margin: '0 auto', color: '#3b82f6' }} />
        <p style={{ marginTop: '20px', color: '#64748b' }}>Loading Orchestration Dashboard...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', backgroundColor: '#f8fafc', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ color: '#0f172a', margin: 0, fontSize: '28px', fontWeight: '700' }}>
            <Zap size={32} style={{ display: 'inline', marginRight: '12px', color: '#3b82f6' }} />
            Orchestration Command Center
          </h1>
          <p style={{ color: '#64748b', margin: '8px 0 0', fontSize: '14px' }}>
            Autonomous workflow orchestration and execution monitoring
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '20px',
            backgroundColor: health?.orchestrator_active ? '#dcfce7' : '#fee2e2'
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: health?.orchestrator_active ? '#10b981' : '#ef4444'
            }} />
            <span style={{ fontSize: '14px', fontWeight: '600', color: health?.orchestrator_active ? '#166534' : '#991b1b' }}>
              {health?.orchestrator_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <button onClick={loadAllData} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '600'
          }}>
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <MetricCard
          title="Active Workflows"
          value={metrics?.active_workflows || 0}
          icon={<Activity size={24} />}
          color="#3b82f6"
        />
        <MetricCard
          title="Pending Approvals"
          value={approvals.length}
          icon={<Clock size={24} />}
          color="#f59e0b"
        />
        <MetricCard
          title="Completed Today"
          value={metrics?.completed_workflows || 0}
          icon={<CheckCircle size={24} />}
          color="#10b981"
        />
        <MetricCard
          title="Failed"
          value={metrics?.failed_workflows || 0}
          icon={<XCircle size={24} />}
          color="#ef4444"
        />
        <MetricCard
          title="Avg Execution Time"
          value={`${(metrics?.avg_execution_time_seconds || 0).toFixed(1)}s`}
          icon={<BarChart3 size={24} />}
          color="#8b5cf6"
        />
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', backgroundColor: 'white', padding: '4px', borderRadius: '12px' }}>
        {['active', 'approvals', 'history', 'actions'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1,
              padding: '12px 20px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px',
              backgroundColor: activeTab === tab ? '#3b82f6' : 'transparent',
              color: activeTab === tab ? 'white' : '#64748b',
              transition: 'all 0.2s'
            }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'approvals' && approvals.length > 0 && (
              <span style={{
                marginLeft: '8px',
                padding: '2px 8px',
                borderRadius: '10px',
                backgroundColor: activeTab === tab ? 'rgba(255,255,255,0.3)' : '#ef4444',
                color: 'white',
                fontSize: '12px'
              }}>
                {approvals.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content Based on Tab */}
      {activeTab === 'active' && (
        <div>
          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 16px', color: '#0f172a' }}>Workflow Status Distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={statusDistribution}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {statusDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase().replace(' ', '_')] || '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <h3 style={{ margin: '0 0 16px', color: '#0f172a' }}>Priority Breakdown</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={priorityDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Workflows List */}
          <div style={{ backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0' }}>
              <h3 style={{ margin: 0, color: '#0f172a' }}>Active Workflows</h3>
            </div>
            {workflows.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                <Activity size={48} style={{ opacity: 0.3 }} />
                <p style={{ marginTop: '12px' }}>No active workflows</p>
              </div>
            ) : (
              <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {workflows.map(workflow => (
                  <WorkflowCard
                    key={workflow.workflow_id}
                    workflow={workflow}
                    onViewDetails={() => setSelectedWorkflow(workflow)}
                    getStatusColor={getStatusColor}
                    getStatusIcon={getStatusIcon}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'approvals' && (
        <div style={{ backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0' }}>
            <h3 style={{ margin: 0, color: '#0f172a' }}>Pending Approvals</h3>
          </div>
          {approvals.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
              <CheckCircle size={48} style={{ opacity: 0.3 }} />
              <p style={{ marginTop: '12px' }}>No pending approvals</p>
            </div>
          ) : (
            <div>
              {approvals.map(approval => (
                <div key={approval.approval_id} style={{
                  padding: '20px',
                  borderBottom: '1px solid #e2e8f0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        backgroundColor: COLORS[approval.risk_level] || '#6b7280',
                        color: 'white',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {approval.risk_level?.toUpperCase()}
                      </span>
                      <span style={{ fontWeight: '600', color: '#0f172a' }}>{approval.workflow_type}</span>
                    </div>
                    <p style={{ margin: '4px 0', color: '#64748b', fontSize: '14px' }}>
                      {approval.action_summary}
                    </p>
                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '12px', color: '#94a3b8' }}>
                      <span>Required Role: <strong>{approval.required_role}</strong></span>
                      <span>Expires: {approval.expires_at ? new Date(approval.expires_at).toLocaleString() : 'N/A'}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => handleApprove(approval.workflow_id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 20px',
                        backgroundColor: '#10b981',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontWeight: '600'
                      }}
                    >
                      <Check size={18} />
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt('Rejection reason:');
                        if (reason) handleReject(approval.workflow_id, reason);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 20px',
                        backgroundColor: '#ef4444',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontWeight: '600'
                      }}
                    >
                      <X size={18} />
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
          <BarChart3 size={48} style={{ opacity: 0.3 }} />
          <p style={{ marginTop: '12px' }}>Workflow history view coming soon...</p>
        </div>
      )}

      {activeTab === 'actions' && (
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 20px', color: '#0f172a' }}>Manual Orchestration Triggers</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
            <ActionButton
              title="Trigger Stockout Mitigation"
              description="Manually trigger stockout mitigation workflow"
              icon={<AlertTriangle size={20} />}
              onClick={() => handleTriggerOrchestration('STOCKOUT_MITIGATION', 'high')}
              color="#ef4444"
            />
            <ActionButton
              title="Inventory Rebalance"
              description="Trigger inventory rebalancing across warehouses"
              icon={<RefreshCw size={20} />}
              onClick={() => handleTriggerOrchestration('INVENTORY_REBALANCE', 'medium')}
              color="#3b82f6"
            />
            <ActionButton
              title="Delay Recovery"
              description="Trigger delivery delay recovery workflow"
              icon={<Clock size={20} />}
              onClick={() => handleTriggerOrchestration('DELAY_RECOVERY', 'medium')}
              color="#f59e0b"
            />
            <ActionButton
              title="Demand Surge Response"
              description="Trigger demand surge response workflow"
              icon={<Activity size={20} />}
              onClick={() => handleTriggerOrchestration('DEMAND_SURGE_RESPONSE', 'high')}
              color="#8b5cf6"
            />
          </div>
        </div>
      )}

      {/* Workflow Details Modal */}
      {selectedWorkflow && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            width: '80%',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <div style={{ padding: '24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between' }}>
              <h3 style={{ margin: 0 }}>Workflow Details: {selectedWorkflow.workflow_id}</h3>
              <button onClick={() => setSelectedWorkflow(null)} style={{ border: 'none', background: 'none', cursor: 'pointer' }}>
                <X size={24} />
              </button>
            </div>
            <div style={{ padding: '24px' }}>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px' }}>
                {JSON.stringify(selectedWorkflow, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper Components
const MetricCard = ({ title, value, icon, color }) => (
  <div style={{
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  }}>
    <div style={{
      width: '48px',
      height: '48px',
      borderRadius: '12px',
      backgroundColor: `${color}15`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: color
    }}>
      {icon}
    </div>
    <div>
      <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>{title}</p>
      <p style={{ margin: '4px 0 0', fontSize: '24px', fontWeight: '700', color: '#0f172a' }}>{value}</p>
    </div>
  </div>
);

const WorkflowCard = ({ workflow, onViewDetails, getStatusColor, getStatusIcon }) => (
  <div style={{
    padding: '16px 20px',
    borderBottom: '1px solid #e2e8f0',
    cursor: 'pointer',
    transition: 'background 0.2s'
  }}
  onClick={onViewDetails}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          backgroundColor: `${getStatusColor(workflow.status)}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: getStatusColor(workflow.status)
        }}>
          {getStatusIcon(workflow.status)}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontWeight: '600', color: '#0f172a' }}>{workflow.workflow_id}</span>
            <span style={{
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: COLORS[workflow.priority] || '#6b7280',
              color: 'white',
              fontSize: '11px',
              fontWeight: '600'
            }}>
              {workflow.priority?.toUpperCase()}
            </span>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
            {workflow.workflow_type?.replace(/_/g, ' ')}
          </p>
        </div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{
          padding: '4px 12px',
          borderRadius: '4px',
          backgroundColor: `${getStatusColor(workflow.status)}15`,
          color: getStatusColor(workflow.status),
          fontSize: '12px',
          fontWeight: '600'
        }}>
          {workflow.status?.toUpperCase().replace(/_/g, ' ')}
        </div>
        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#94a3b8' }}>
          {workflow.steps?.length || 0} steps
        </p>
      </div>
    </div>
  </div>
);

const ActionButton = ({ title, description, icon, onClick, color }) => (
  <button
    onClick={onClick}
    style={{
      padding: '20px',
      borderRadius: '12px',
      border: '2px solid #e2e8f0',
      backgroundColor: 'white',
      cursor: 'pointer',
      textAlign: 'left',
      transition: 'all 0.2s'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = color;
      e.currentTarget.style.boxShadow = `0 4px 12px ${color}30`;
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = '#e2e8f0';
      e.currentTarget.style.boxShadow = 'none';
    }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
      <div style={{ color: color }}>{icon}</div>
      <span style={{ fontWeight: '600', color: '#0f172a', fontSize: '15px' }}>{title}</span>
    </div>
    <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>{description}</p>
  </button>
);

export default Orchestration;
