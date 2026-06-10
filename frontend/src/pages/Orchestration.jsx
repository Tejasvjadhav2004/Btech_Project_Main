import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, AlertTriangle, CheckCircle, Clock, XCircle, Loader, Play, Pause,
  ChevronDown, ChevronUp, RefreshCw, Check, X, Zap, BarChart3, Cpu
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import AnimatedCounter from '../components/ui/AnimatedCounter';
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
    const interval = setInterval(loadAllData, 30000);
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
    return <div className="space-y-4"><LoadingSkeleton variant="kpi" count={4} /><LoadingSkeleton variant="table" /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Cpu size={24} className="text-accent-cyan" /> Orchestration Engine
          </h1>
          <p className="text-sm text-text-muted mt-1">Autonomous workflow orchestration and execution monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${health?.orchestrator_active ? 'bg-severity-healthy/20' : 'bg-severity-critical/20'}`}>
            <span className={`status-dot ${health?.orchestrator_active ? 'bg-severity-healthy' : 'bg-severity-critical'}`} />
            <span className={`text-xs font-medium ${health?.orchestrator_active ? 'text-severity-healthy' : 'text-severity-critical'}`}>
              {health?.orchestrator_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <button onClick={loadAllData} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-accent-blue/15 border border-accent-blue/25 text-accent-blue text-sm font-medium hover:bg-accent-blue/25 transition-all">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard>
          <p className="text-[10px] uppercase text-text-muted font-semibold">Active Workflows</p>
          <p className="text-2xl font-bold text-accent-blue mt-1"><AnimatedCounter value={metrics?.active_workflows || 0} decimals={0} /></p>
        </GlassCard>
        <GlassCard>
          <p className="text-[10px] uppercase text-text-muted font-semibold">Pending Approvals</p>
          <p className="text-2xl font-bold text-severity-high mt-1"><AnimatedCounter value={approvals.length} decimals={0} /></p>
        </GlassCard>
        <GlassCard>
          <p className="text-[10px] uppercase text-text-muted font-semibold">Completed Today</p>
          <p className="text-2xl font-bold text-severity-healthy mt-1"><AnimatedCounter value={metrics?.completed_workflows || 0} decimals={0} /></p>
        </GlassCard>
        <GlassCard>
          <p className="text-[10px] uppercase text-text-muted font-semibold">Failed</p>
          <p className="text-2xl font-bold text-severity-critical mt-1"><AnimatedCounter value={metrics?.failed_workflows || 0} decimals={0} /></p>
        </GlassCard>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2">
        {['active', 'approvals', 'actions'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${activeTab === tab ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/25' : 'border border-glass-border text-text-muted hover:bg-glass-bg'}`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
            {tab === 'approvals' && approvals.length > 0 && (
              <span className="ml-2 px-1.5 py-0.5 rounded bg-severity-critical text-white text-[10px]">{approvals.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content Based on Tab */}
      {activeTab === 'active' && (
        <div className="space-y-6">
          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GlassCard hover={false}>
              <h3 className="text-sm font-semibold text-text-primary mb-4">Workflow Status Distribution</h3>
              {statusDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={statusDistribution} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      {statusDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase().replace(' ', '_')] || '#6b7280'} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="text-center py-8 text-text-muted text-sm">No workflow data</div>
              )}
            </GlassCard>

            <GlassCard hover={false}>
              <h3 className="text-sm font-semibold text-text-primary mb-4">Priority Breakdown</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={priorityDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </GlassCard>
          </div>

          {/* Workflows List */}
          <GlassCard padding="p-0" hover={false}>
            <div className="px-4 py-3 border-b border-glass-border">
              <h3 className="text-sm font-semibold text-text-primary">Active Workflows</h3>
            </div>
            {workflows.length === 0 ? (
              <div className="text-center py-12 text-text-muted text-sm">
                <Activity size={32} className="mx-auto mb-3 opacity-30" />
                No active workflows
              </div>
            ) : (
              <div className="max-h-[500px] overflow-y-auto">
                {workflows.map((workflow, i) => (
                  <motion.div
                    key={workflow.workflow_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    onClick={() => setSelectedWorkflow(workflow)}
                    className="px-4 py-3 border-b border-glass-border/50 hover:bg-bg-card-hover cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center`} style={{ backgroundColor: `${getStatusColor(workflow.status)}20`, color: getStatusColor(workflow.status) }}>
                          {getStatusIcon(workflow.status)}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-text-primary">{workflow.workflow_id}</span>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold text-white" style={{ backgroundColor: COLORS[workflow.priority] || '#6b7280' }}>
                              {workflow.priority?.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-xs text-text-muted mt-0.5">{workflow.workflow_type?.replace(/_/g, ' ')}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="px-2 py-1 rounded text-xs font-semibold" style={{ backgroundColor: `${getStatusColor(workflow.status)}20`, color: getStatusColor(workflow.status) }}>
                          {workflow.status?.toUpperCase().replace(/_/g, ' ')}
                        </div>
                        <p className="text-[10px] text-text-dim mt-1">{workflow.steps?.length || 0} steps</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>
      )}

      {activeTab === 'approvals' && (
        <GlassCard padding="p-0" hover={false}>
          <div className="px-4 py-3 border-b border-glass-border">
            <h3 className="text-sm font-semibold text-text-primary">Pending Approvals</h3>
          </div>
          {approvals.length === 0 ? (
            <div className="text-center py-12 text-text-muted text-sm">
              <CheckCircle size={32} className="mx-auto mb-3 opacity-30" />
              No pending approvals
            </div>
          ) : (
            <div>
              {approvals.map((approval, i) => (
                <motion.div
                  key={approval.approval_id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="p-4 border-b border-glass-border/50"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold text-white" style={{ backgroundColor: COLORS[approval.risk_level] || '#6b7280' }}>
                          {approval.risk_level?.toUpperCase()}
                        </span>
                        <span className="text-sm font-semibold text-text-primary">{approval.workflow_type}</span>
                      </div>
                      <p className="text-xs text-text-secondary mb-2">{approval.action_summary}</p>
                      <div className="flex gap-4 text-[10px] text-text-muted">
                        <span>Required: <span className="text-text-secondary">{approval.required_role}</span></span>
                        <span>Expires: <span className="text-text-secondary">{approval.expires_at ? new Date(approval.expires_at).toLocaleString() : 'N/A'}</span></span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(approval.workflow_id)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-severity-healthy/20 text-severity-healthy text-xs font-medium hover:bg-severity-healthy/30 transition-colors"
                      >
                        <Check size={14} /> Approve
                      </button>
                      <button
                        onClick={() => {
                          const reason = prompt('Rejection reason:');
                          if (reason) handleReject(approval.workflow_id, reason);
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-severity-critical/20 text-severity-critical text-xs font-medium hover:bg-severity-critical/30 transition-colors"
                      >
                        <X size={14} /> Reject
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {activeTab === 'actions' && (
        <GlassCard>
          <h3 className="text-sm font-semibold text-text-primary mb-4">Manual Orchestration Triggers</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: 'Stockout Mitigation', desc: 'Manually trigger stockout mitigation workflow', icon: AlertTriangle, color: 'text-severity-critical', action: () => handleTriggerOrchestration('STOCKOUT_MITIGATION', 'high') },
              { title: 'Inventory Rebalance', desc: 'Trigger inventory rebalancing across warehouses', icon: RefreshCw, color: 'text-accent-blue', action: () => handleTriggerOrchestration('INVENTORY_REBALANCE', 'medium') },
              { title: 'Delay Recovery', desc: 'Trigger delivery delay recovery workflow', icon: Clock, color: 'text-severity-high', action: () => handleTriggerOrchestration('DELAY_RECOVERY', 'medium') },
              { title: 'Demand Surge Response', desc: 'Trigger demand surge response workflow', icon: Activity, color: 'text-accent-purple', action: () => handleTriggerOrchestration('DEMAND_SURGE_RESPONSE', 'high') },
            ].map((btn, i) => (
              <button
                key={i}
                onClick={btn.action}
                className="p-4 rounded-lg border border-glass-border bg-bg-card hover:bg-bg-card-hover text-left transition-all hover:border-accent-blue/30"
              >
                <div className="flex items-center gap-2 mb-2">
                  <btn.icon size={18} className={btn.color} />
                  <span className="text-sm font-semibold text-text-primary">{btn.title}</span>
                </div>
                <p className="text-xs text-text-muted">{btn.desc}</p>
              </button>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Workflow Details Modal */}
      {selectedWorkflow && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setSelectedWorkflow(null)}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass rounded-xl w-[90%] max-w-2xl max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-glass-border">
              <h3 className="text-sm font-semibold text-text-primary">Workflow: {selectedWorkflow.workflow_id}</h3>
              <button onClick={() => setSelectedWorkflow(null)} className="text-text-muted hover:text-text-primary transition-colors">
                <X size={20} />
              </button>
            </div>
            <div className="p-5 overflow-y-auto max-h-[60vh]">
              <pre className="text-xs text-text-secondary bg-bg-primary/50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(selectedWorkflow, null, 2)}
              </pre>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Orchestration;
