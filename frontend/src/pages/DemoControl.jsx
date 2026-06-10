import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play, Square, RotateCcw, Brain, Gauge, Truck, Package, TrendingUp, TrendingDown,
  Zap, AlertTriangle, CheckCircle, Eye, Radio, Activity, ShoppingCart,
  ArrowLeftRight, Clock, Loader, X, Workflow, Bot, Shield
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import KPICard from '../components/ui/KPICard';
import StatusBadge from '../components/ui/StatusBadge';
import AIThinkingIndicator from '../components/ui/AIThinkingIndicator';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import DemoComparison from '../components/DemoComparison';
import {
  startDemoSimulation, stopDemoSimulation, setDemoMode, triggerDemoScenario,
  getDemoStatus, getDemoMetrics, getDemoActivities, getDemoScenarios,
  resetDemo, getActivityDetail
} from '../services/api';

const DemoControl = () => {
  const [simState, setSimState] = useState({ is_running: false, mode: 'ai_autonomous', tick_count: 0, signals_generated: 0, actions_executed: 0 });
  const [metrics, setMetrics] = useState(null);
  const [activities, setActivities] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [activityDetail, setActivityDetail] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => { fetchStatus(); fetchScenarios(); }, []);

  const connectWebSocket = useCallback(() => {
    const wsUrl = `${import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000'}/api/demo/ws`;
    try {
      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'simulation_update') { setSimState(data.data.state); setMetrics(data.data.metrics); setActivities(data.data.activities || []); }
          else if (data.type === 'mode_changed') setSimState(p => ({ ...p, mode: data.mode }));
          else if (data.type === 'scenario_triggered') fetchStatus();
        } catch (e) {}
      };
      wsRef.current.onclose = () => { setTimeout(connectWebSocket, 3000); };
    } catch (e) {}
  }, []);

  useEffect(() => {
    if (simState.is_running) connectWebSocket();
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, [simState.is_running, connectWebSocket]);

  const fetchStatus = async () => { try { const d = await getDemoStatus(); setSimState(d.simulation?.state || simState); setMetrics(d.metrics || null); } catch (e) {} };
  const fetchScenarios = async () => { try { const d = await getDemoScenarios(); setScenarios(d.scenarios || []); } catch (e) {} };

  const handleStart = async (mode = 'ai_autonomous') => {
    setLoading(true); setError(null);
    try { const r = await startDemoSimulation(mode); if (r.success) setSimState(r.state); else setError(r.message || 'Failed'); } catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  const handleStop = async () => { setLoading(true); try { const r = await stopDemoSimulation(); if (r.success) setSimState(r.final_state); } catch (e) { setError(e.message); } finally { setLoading(false); } };
  const handleMode = async (mode) => { setLoading(true); try { const r = await setDemoMode(mode); if (r.success) setSimState(p => ({ ...p, mode })); } catch (e) { setError(e.message); } finally { setLoading(false); } };
  const handleScenario = async (id) => { setLoading(true); try { await triggerDemoScenario(id); } catch (e) { setError(e.message); } finally { setLoading(false); } };
  const handleReset = async () => { setLoading(true); try { await resetDemo(); await fetchStatus(); setActivities([]); } catch (e) { setError(e.message); } finally { setLoading(false); } };

  const handleActivityClick = async (activity) => {
    try { const r = await getActivityDetail(activity.id); if (r.success) { setActivityDetail(r.activity); setSelectedActivity(activity); } } catch (e) {}
  };

  const getActivityIcon = (type) => {
    const icons = { signal: AlertTriangle, action: CheckCircle, orders: ShoppingCart, delivery: Truck, forecasting: TrendingUp, optimization: Gauge, orchestration: Brain, scenario: Zap };
    const Icon = icons[type] || Activity;
    const colors = { signal: 'text-severity-high', action: 'text-severity-healthy', orders: 'text-accent-blue', delivery: 'text-accent-purple', forecasting: 'text-accent-cyan', optimization: 'text-accent-pink', orchestration: 'text-accent-purple', scenario: 'text-severity-critical' };
    return <Icon size={16} className={colors[type] || 'text-text-muted'} />;
  };

  const kpis = metrics?.kpis || {};
  const improvements = metrics?.improvements || {};
  const spark = (b, v) => Array.from({ length: 12 }, () => b + (Math.random() - 0.5) * v);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Brain size={24} className="text-accent-purple" />
            Simulation Command Center
          </h1>
          <p className="text-sm text-text-muted mt-1">Real-time AI-powered autonomous supply chain simulation</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge type={simState.mode === 'ai_autonomous' ? 'ai' : 'warning'} size="md" />
          <StatusBadge type={simState.is_running ? 'running' : 'stopped'} pulse={simState.is_running} size="md" />
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex items-center gap-3 p-3 rounded-lg bg-severity-critical/10 border border-severity-critical/20 text-severity-critical text-sm">
            <AlertTriangle size={16} /><span className="flex-1">{error}</span>
            <button onClick={() => setError(null)}><X size={14} /></button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Controls */}
        <div className="lg:col-span-3 space-y-4">
          {/* Simulation Controls */}
          <GlassCard padding="p-4" hover={false}>
            <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
              <Radio size={16} className="text-accent-cyan" /> Controls
            </h3>
            <div className="space-y-2">
              {!simState.is_running ? (
                <button onClick={() => handleStart('ai_autonomous')} disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-severity-healthy/15 border border-severity-healthy/30 text-severity-healthy font-semibold text-sm hover:bg-severity-healthy/25 hover:shadow-[0_0_20px_rgba(16,185,129,0.2)] transition-all duration-300 disabled:opacity-50">
                  {loading ? <Loader size={18} className="animate-spin" /> : <Play size={18} />} Run Autonomous System
                </button>
              ) : (
                <button onClick={handleStop} disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-severity-critical/15 border border-severity-critical/30 text-severity-critical font-semibold text-sm hover:bg-severity-critical/25 hover:shadow-[0_0_20px_rgba(239,68,68,0.2)] transition-all duration-300 disabled:opacity-50">
                  {loading ? <Loader size={18} className="animate-spin" /> : <Square size={18} />} Stop Simulation
                </button>
              )}
              <button onClick={handleReset} disabled={loading}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-glass-border text-text-muted text-xs hover:bg-glass-bg hover:text-text-secondary transition-all">
                <RotateCcw size={14} /> Reset Demo
              </button>
            </div>

            {/* Mode Toggle */}
            <div className="mt-4 pt-4 border-t border-glass-border">
              <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Operating Mode</p>
              <div className="grid grid-cols-2 gap-2">
                <button onClick={() => handleMode('baseline')} disabled={!simState.is_running}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${simState.mode === 'baseline' ? 'bg-severity-high/20 text-severity-high border border-severity-high/30' : 'border border-glass-border text-text-muted hover:bg-glass-bg'} disabled:opacity-30`}>
                  Baseline
                </button>
                <button onClick={() => handleMode('ai_autonomous')} disabled={!simState.is_running}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 ${simState.mode === 'ai_autonomous' ? 'bg-accent-purple/20 text-accent-purple border border-accent-purple/30' : 'border border-glass-border text-text-muted hover:bg-glass-bg'} disabled:opacity-30`}>
                  AI Autonomous
                </button>
              </div>
            </div>

            {/* Scenarios */}
            <div className="mt-4 pt-4 border-t border-glass-border">
              <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Demo Scenarios</p>
              <div className="space-y-1.5">
                {scenarios.map((s) => (
                  <button key={s.id} onClick={() => handleScenario(s.id)} disabled={!simState.is_running || loading}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-severity-critical/20 text-severity-critical/80 text-xs text-left hover:bg-severity-critical/10 hover:border-severity-critical/40 hover:shadow-[0_0_12px_rgba(239,68,68,0.1)] transition-all duration-200 disabled:opacity-30">
                    <Zap size={12} />{s.name}
                  </button>
                ))}
              </div>
            </div>
          </GlassCard>

          {/* Stats */}
          <GlassCard padding="p-4" hover={false}>
            <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
              <Gauge size={16} className="text-accent-blue" /> AI Stats
            </h3>
            <div className="space-y-3">
              {[
                { label: 'AI Cycles', value: simState.tick_count, color: 'text-text-primary' },
                { label: 'Signals', value: simState.signals_generated, color: 'text-severity-high' },
                { label: 'Actions', value: simState.actions_executed, color: 'text-severity-healthy' },
              ].map((s, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-xs text-text-muted">{s.label}</span>
                  <span className={`text-lg font-bold font-mono ${s.color}`}><AnimatedCounter value={s.value} decimals={0} /></span>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Comparison Button */}
          <button onClick={() => setShowComparison(!showComparison)}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-accent-purple/10 border border-accent-purple/20 text-accent-purple font-medium text-sm hover:bg-accent-purple/20 hover:shadow-[0_0_20px_rgba(139,92,246,0.15)] transition-all">
            <ArrowLeftRight size={16} />{showComparison ? 'Hide' : 'Show'} Comparison
          </button>
        </div>

        {/* Center: AI Feed */}
        <div className="lg:col-span-5">
          <GlassCard className="h-[calc(100vh-180px)]" glowColor="purple" padding="p-0" hover={false}>
            <div className="p-4 border-b border-glass-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain size={18} className="text-accent-purple" />
                <h2 className="text-sm font-semibold text-text-primary">AI Intelligence Feed</h2>
              </div>
              <div className="flex items-center gap-2">
                <span className="status-dot status-dot-live bg-severity-healthy" />
                <span className="text-[10px] text-text-muted font-mono">LIVE</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2" style={{ height: 'calc(100% - 56px)' }}>
              {activities.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-text-muted">
                  <Brain size={40} className="opacity-20 mb-3" />
                  <p className="text-sm">Start simulation to see AI operations</p>
                </div>
              ) : (
                activities.map((a, i) => (
                  <motion.div key={a.id || i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.02 }}
                    onClick={() => handleActivityClick(a)}
                    className={`flex gap-3 p-3 rounded-lg bg-bg-card hover:bg-bg-card-hover border-l-2 ${a.severity === 'error' ? 'border-severity-critical' : a.severity === 'warning' ? 'border-severity-high' : a.severity === 'success' ? 'border-severity-healthy' : 'border-accent-blue'} transition-all duration-200 cursor-pointer group`}>
                    <div className="mt-0.5 shrink-0">{getActivityIcon(a.type)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary group-hover:text-accent-blue transition-colors">{a.message}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <StatusBadge type={a.type || 'info'} size="xs" />
                        <span className="text-[10px] text-text-dim font-mono">{a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}</span>
                      </div>
                    </div>
                    <Eye size={12} className="text-text-dim opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
                  </motion.div>
                ))
              )}
            </div>
          </GlassCard>
        </div>

        {/* Right: KPIs */}
        <div className="lg:col-span-4">
          <GlassCard className="h-[calc(100vh-180px)] overflow-y-auto" padding="p-4" hover={false}>
            <div className="flex items-center gap-2 mb-4">
              <Gauge size={18} className="text-accent-cyan" />
              <h2 className="text-sm font-semibold text-text-primary">Live Metrics</h2>
            </div>

            {kpis.forecasting || kpis.delivery || kpis.inventory ? (
              <div className="space-y-5">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Forecasting</p>
                  <div className="grid grid-cols-2 gap-2">
                    <KPICard title="MAE" value={kpis.forecasting?.mae?.value || 0} unit="units" target="< 15" status={kpis.forecasting?.mae?.status} icon={<Activity size={12} />} sparklineData={spark(12, 4)} />
                    <KPICard title="RMSE" value={kpis.forecasting?.rmse?.value || 0} unit="units" target="< 20" status={kpis.forecasting?.rmse?.status} icon={<TrendingDown size={12} />} sparklineData={spark(17, 5)} />
                  </div>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Delivery</p>
                  <div className="grid grid-cols-2 gap-2">
                    <KPICard title="Avg Delay" value={kpis.delivery?.avg_delay_days?.value || 0} unit="days" target="< 2" status={kpis.delivery?.avg_delay_days?.status} icon={<Clock size={12} />} />
                    <KPICard title="On-Time" value={kpis.delivery?.on_time_pct?.value || 0} unit="%" target="> 80%" status={kpis.delivery?.on_time_pct?.status} icon={<Truck size={12} />} />
                  </div>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Inventory</p>
                  <div className="grid grid-cols-2 gap-2">
                    <KPICard title="Utilization" value={kpis.inventory?.stock_utilization_pct?.value || 0} unit="%" target="> 75%" status={kpis.inventory?.stock_utilization_pct?.status} icon={<Package size={12} />} />
                    <KPICard title="Stock-Out" value={kpis.inventory?.stock_out_rate_pct?.value || 0} unit="%" target="< 12%" status={kpis.inventory?.stock_out_rate_pct?.status} icon={<AlertTriangle size={12} />} />
                  </div>
                </div>
                {improvements && Object.keys(improvements).length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 font-semibold">Improvements vs Baseline</p>
                    <div className="grid grid-cols-2 gap-2">
                      {[
                        { label: 'MAE', val: improvements.mae_reduction_pct, icon: TrendingDown },
                        { label: 'Delay', val: improvements.delay_reduction_pct, icon: TrendingDown },
                        { label: 'On-Time', val: improvements.on_time_improvement_pct, icon: TrendingUp, positive: true },
                        { label: 'Stockout', val: improvements.stockout_reduction_pct, icon: TrendingDown },
                      ].map((item, i) => (
                        <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-severity-healthy/8 border border-severity-healthy/15">
                          <item.icon size={12} className="text-severity-healthy" />
                          <span className="text-[10px] text-severity-healthy font-medium">
                            {item.positive ? '+' : '-'}{item.val || 0}% {item.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-text-muted">
                <Gauge size={32} className="opacity-20 mb-2" />
                <p className="text-sm">Start simulation for live metrics</p>
              </div>
            )}
          </GlassCard>
        </div>
      </div>

      {/* Comparison Panel */}
      <AnimatePresence>
        {showComparison && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <DemoComparison />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Activity Detail Modal */}
      <AnimatePresence>
        {selectedActivity && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => { setSelectedActivity(null); setActivityDetail(null); }} />
            <motion.div initial={{ scale: 0.95, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.95, y: 20 }}
              className="relative glass rounded-2xl p-6 w-[600px] max-w-[90vw] max-h-[80vh] overflow-y-auto border border-glass-border" style={{ background: 'rgba(15,22,41,0.95)' }}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  {getActivityIcon(selectedActivity.type)}
                  <h3 className="text-lg font-bold text-text-primary">{selectedActivity.type?.toUpperCase()} Details</h3>
                </div>
                <button onClick={() => { setSelectedActivity(null); setActivityDetail(null); }} className="p-2 rounded-lg hover:bg-glass-bg text-text-muted"><X size={18} /></button>
              </div>
              <p className="text-sm text-text-secondary mb-4">{selectedActivity.message}</p>
              {activityDetail?.ai_reasoning && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-accent-purple flex items-center gap-2 mb-2"><Brain size={14} /> AI Decision Process</h4>
                  <div className="space-y-1.5">
                    {activityDetail.ai_reasoning.decision_process?.map((step, i) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-text-secondary"><CheckCircle size={12} className="text-severity-healthy mt-0.5 shrink-0" />{step}</div>
                    ))}
                  </div>
                  <div className="flex gap-2 mt-2">
                    <span className="px-2 py-0.5 rounded-full bg-severity-healthy/15 text-severity-healthy text-[10px] font-medium">
                      Confidence: {((activityDetail.ai_reasoning.confidence || 0) * 100).toFixed(0)}%
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-accent-blue/15 text-accent-blue text-[10px] font-medium">
                      {activityDetail.ai_reasoning.execution_time_ms}ms
                    </span>
                  </div>
                </div>
              )}
              {activityDetail?.orchestration_flow && (
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-accent-purple flex items-center gap-2 mb-2"><Workflow size={14} /> Orchestration Flow</h4>
                  <div className="space-y-1.5">
                    {activityDetail.orchestration_flow.steps?.map((step, i) => (
                      <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-bg-card">
                        <div className="flex items-center gap-2">
                          {step.status === 'completed' ? <CheckCircle size={14} className="text-severity-healthy" /> : <Loader size={14} className="text-accent-purple animate-spin" />}
                          <span className="text-xs text-text-primary">{step.step}</span>
                        </div>
                        <span className="text-[10px] text-text-dim font-mono">{step.duration_ms}ms</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="text-[10px] text-text-dim mt-4 pt-3 border-t border-glass-border font-mono">
                {new Date(selectedActivity.timestamp).toLocaleString()}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DemoControl;
