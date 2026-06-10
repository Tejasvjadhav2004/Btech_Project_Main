import React, { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, LineChart, Line
} from 'recharts';
import {
  Activity, AlertTriangle, Box, Brain, Clock, Cpu, Gauge, Package,
  Radio, ShoppingCart, TrendingDown, TrendingUp, Truck, Warehouse, Zap,
  Shield, Eye, ArrowRight, CheckCircle, Loader
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import KPICard from '../components/ui/KPICard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import AIThinkingIndicator from '../components/ui/AIThinkingIndicator';
import TimelineStep from '../components/ui/TimelineStep';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import {
  getDashboardOverview, getDashboardWarehouseStock, getDashboardLowStock,
  getDashboardMetrics, getActiveSignals, getDemoStatus, getDemoActivities,
  getDemoMetrics, getSignalStats
} from '../services/api';

// Dark tooltip for Recharts
const DarkTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 border border-glass-border text-xs" style={{ background: 'rgba(15,22,41,0.95)' }}>
      <p className="text-text-muted mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="font-medium">
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </p>
      ))}
    </div>
  );
};

const Dashboard = ({ userRole }) => {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [warehouseStock, setWarehouseStock] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [signals, setSignals] = useState([]);
  const [signalStats, setSignalStats] = useState(null);
  const [demoStatus, setDemoStatus] = useState(null);
  const [activities, setActivities] = useState([]);
  const [demoMetrics, setDemoMetrics] = useState(null);
  const wsRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [ov, wh, ls, met, sig, ss, ds, acts, dm] = await Promise.all([
        getDashboardOverview(), getDashboardWarehouseStock(), getDashboardLowStock(),
        getDashboardMetrics(), getActiveSignals(), getSignalStats(),
        getDemoStatus(), getDemoActivities(20), getDemoMetrics()
      ]);
      setOverview(ov);
      setWarehouseStock(wh?.warehouses || []);
      setLowStock(ls?.items || []);
      setMetrics(met || {});
      setSignals(sig?.signals || []);
      setSignalStats(ss);
      setDemoStatus(ds);
      setActivities(acts?.activities || []);
      setDemoMetrics(dm);
    } catch (e) {
      console.error('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // WebSocket for live updates
  useEffect(() => {
    const wsUrl = `${import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000'}/api/demo/ws`;
    try {
      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'simulation_update') {
            setDemoMetrics(data.data.metrics);
            if (data.data.activities) setActivities(data.data.activities.slice(0, 20));
          }
        } catch (e) {}
      };
      wsRef.current.onerror = () => {};
      wsRef.current.onclose = () => {};
    } catch (e) {}
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton variant="kpi" count={7} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LoadingSkeleton variant="chart" className="lg:col-span-2" />
          <LoadingSkeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  const kpis = demoMetrics?.kpis || {};
  const improvements = demoMetrics?.improvements || {};
  const simState = demoStatus?.simulation?.state || {};

  // Generate sparkline mock data
  const spark = (base, variance) => Array.from({ length: 12 }, () => base + (Math.random() - 0.5) * variance);

  // Warehouse chart data
  const whChartData = warehouseStock.map(w => ({
    name: (w.warehouse_id || w.name || '').slice(0, 8),
    utilization: w.utilization_rate || w.utilization || 0,
    stock: w.current_utilization || 0,
  }));

  // Timeline steps
  const timelineSteps = [
    { label: 'Signal', status: signals.length > 0 ? 'completed' : 'pending', duration: '0.2s' },
    { label: 'AI Analysis', status: signals.length > 0 ? 'completed' : 'pending', duration: '1.1s' },
    { label: 'Optimization', status: simState.actions_executed > 0 ? 'completed' : signals.length > 0 ? 'active' : 'pending', duration: '2.4s' },
    { label: 'LLM Decision', status: simState.actions_executed > 0 ? 'completed' : 'pending', duration: '3.2s' },
    { label: 'Validation', status: simState.actions_executed > 0 ? 'completed' : 'pending', duration: '0.5s' },
    { label: 'Execution', status: simState.is_running ? 'active' : simState.actions_executed > 0 ? 'completed' : 'pending', duration: '1.8s' },
    { label: 'Resolution', status: simState.actions_executed > 5 ? 'completed' : 'pending' },
  ];

  const getActivityIcon = (type) => {
    const icons = { signal: AlertTriangle, action: CheckCircle, orders: ShoppingCart, delivery: Truck, forecasting: TrendingUp, optimization: Gauge, orchestration: Brain, scenario: Zap };
    const Icon = icons[type] || Activity;
    const colors = { signal: 'text-severity-high', action: 'text-severity-healthy', orders: 'text-accent-blue', delivery: 'text-accent-purple', forecasting: 'text-accent-cyan', optimization: 'text-accent-pink', orchestration: 'text-accent-purple', scenario: 'text-severity-critical' };
    return <Icon size={16} className={colors[type] || 'text-text-muted'} />;
  };

  const getSeverityColor = (severity) => {
    const m = { error: 'border-severity-critical', warning: 'border-severity-high', success: 'border-severity-healthy' };
    return m[severity] || 'border-accent-blue';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Radio size={24} className="text-accent-cyan" />
            AI Command Center
          </h1>
          <p className="text-sm text-text-muted mt-1">Autonomous supply chain operations — real-time monitoring & intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge type={simState.is_running ? 'running' : 'stopped'} pulse={simState.is_running} size="md" />
          <span className="text-xs text-text-dim font-mono">
            {simState.mode === 'ai_autonomous' ? 'AI MODE' : 'BASELINE'}
          </span>
        </div>
      </div>

      {/* ===== SECTION 1: KPI STRIP ===== */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <KPICard title="MAE" value={kpis.forecasting?.mae?.value || overview?.mae || 12.4} unit="units" trend="down" trendValue="-18%" status={kpis.forecasting?.mae?.status || 'good'} icon={<Activity size={14} />} sparklineData={spark(12, 4)} target="< 15" delay={0} />
        <KPICard title="RMSE" value={kpis.forecasting?.rmse?.value || overview?.rmse || 16.8} unit="units" trend="down" trendValue="-15%" status={kpis.forecasting?.rmse?.status || 'good'} icon={<TrendingDown size={14} />} sparklineData={spark(17, 5)} target="< 20" delay={0.05} />
        <KPICard title="On-Time" value={kpis.delivery?.on_time_pct?.value || 87.5} unit="%" trend="up" trendValue={`+${improvements.on_time_improvement_pct || 12}%`} status={kpis.delivery?.on_time_pct?.status || 'good'} icon={<Truck size={14} />} sparklineData={spark(85, 10)} target="> 80%" delay={0.1} />
        <KPICard title="Avg Delay" value={kpis.delivery?.avg_delay_days?.value || 1.2} unit="days" trend="down" trendValue={`-${improvements.delay_reduction_pct || 40}%`} status={kpis.delivery?.avg_delay_days?.status || 'good'} icon={<Clock size={14} />} sparklineData={spark(2, 1.5)} target="< 2" delay={0.15} />
        <KPICard title="Stock Util" value={kpis.inventory?.stock_utilization_pct?.value || overview?.warehouse_utilization || 78} unit="%" trend="up" trendValue="+8%" status={kpis.inventory?.stock_utilization_pct?.status || 'good'} icon={<Warehouse size={14} />} sparklineData={spark(75, 12)} target="> 75%" delay={0.2} />
        <KPICard title="Stock-Out" value={kpis.inventory?.stock_out_rate_pct?.value || 5.2} unit="%" trend="down" trendValue={`-${improvements.stockout_reduction_pct || 35}%`} status={kpis.inventory?.stock_out_rate_pct?.status || 'good'} icon={<Package size={14} />} sparklineData={spark(8, 4)} target="< 12%" delay={0.25} />
        <KPICard title="Response" value={kpis.ai_response?.avg_response_time_minutes?.value || 3.5} unit="min" trend="down" trendValue={`-${improvements.response_time_reduction_pct || 60}%`} status={kpis.ai_response?.avg_response_time_minutes?.status || 'good'} icon={<Zap size={14} />} sparklineData={spark(5, 3)} target="< 10 min" delay={0.3} />
      </div>

      {/* ===== SECTION 2 & 3: AI FEED + SIGNALS ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Live AI Orchestration Feed */}
        <GlassCard className="lg:col-span-3" glowColor="purple" padding="p-0" hover={false} delay={0.1}>
          <div className="p-4 border-b border-glass-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain size={18} className="text-accent-purple" />
              <h2 className="text-sm font-semibold text-text-primary">Live AI Orchestration Feed</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="status-dot status-dot-live bg-severity-healthy" />
              <span className="text-[10px] text-text-muted font-mono">LIVE</span>
            </div>
          </div>
          <div className="h-[380px] overflow-y-auto p-3 space-y-2">
            {activities.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-text-muted">
                <Brain size={32} className="opacity-30 mb-2" />
                <p className="text-sm">Start simulation to see AI operations</p>
              </div>
            ) : (
              <AnimatePresence>
                {activities.map((a, i) => (
                  <motion.div
                    key={a.id || i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className={`flex gap-3 p-3 rounded-lg bg-bg-card hover:bg-bg-card-hover border-l-2 ${getSeverityColor(a.severity)} transition-all duration-200 cursor-pointer group`}
                  >
                    <div className="mt-0.5 shrink-0">{getActivityIcon(a.type)}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary group-hover:text-accent-blue transition-colors">{a.message}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <StatusBadge type={a.type || 'info'} size="xs" />
                        <span className="text-[10px] text-text-dim font-mono">
                          {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}
                        </span>
                      </div>
                    </div>
                    <Eye size={12} className="text-text-dim opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>
        </GlassCard>

        {/* Signals & Alerts Panel */}
        <GlassCard className="lg:col-span-2" glowColor="amber" padding="p-0" hover={false} delay={0.15}>
          <div className="p-4 border-b border-glass-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-severity-high" />
              <h2 className="text-sm font-semibold text-text-primary">Active Signals</h2>
            </div>
            <span className="text-xs font-mono text-severity-high">{signals.length} active</span>
          </div>
          <div className="h-[380px] overflow-y-auto p-3 space-y-2">
            {signals.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-text-muted">
                <Shield size={32} className="opacity-30 mb-2" />
                <p className="text-sm">No active signals</p>
              </div>
            ) : (
              signals.slice(0, 15).map((sig, i) => (
                <motion.div
                  key={sig.signal_id || i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-3 rounded-lg bg-bg-card hover:bg-bg-card-hover transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <StatusBadge type={sig.type?.toLowerCase() || 'info'} pulse size="xs" />
                    <StatusBadge type={sig.severity?.toLowerCase() || 'medium'} size="xs" />
                  </div>
                  <p className="text-xs text-text-secondary line-clamp-2">{sig.message}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-[10px] text-text-dim">{sig.entity_id}</span>
                    <span className="text-[10px] text-text-dim font-mono">
                      {sig.created_at ? new Date(sig.created_at).toLocaleTimeString() : ''}
                    </span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </GlassCard>
      </div>

      {/* ===== SECTION 4: OPERATIONAL MONITORING ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Warehouse Utilization */}
        <GlassCard className="lg:col-span-2" delay={0.2}>
          <div className="flex items-center gap-2 mb-4">
            <Warehouse size={18} className="text-accent-cyan" />
            <h2 className="text-sm font-semibold text-text-primary">Warehouse Utilization & Stock</h2>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={whChartData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <Bar dataKey="utilization" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Utilization %" />
              <Bar dataKey="stock" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Stock Units" />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* AI Operations Summary */}
        <GlassCard glowColor="blue" delay={0.25}>
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={18} className="text-accent-blue" />
            <h2 className="text-sm font-semibold text-text-primary">AI Operations</h2>
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">AI Cycles</span>
              <span className="text-lg font-bold text-text-primary font-mono"><AnimatedCounter value={simState.tick_count || 0} decimals={0} /></span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Signals Detected</span>
              <span className="text-lg font-bold text-severity-high font-mono"><AnimatedCounter value={simState.signals_generated || signalStats?.total_signals || 0} decimals={0} /></span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Actions Executed</span>
              <span className="text-lg font-bold text-severity-healthy font-mono"><AnimatedCounter value={simState.actions_executed || 0} decimals={0} /></span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Total Products</span>
              <span className="text-lg font-bold text-accent-blue font-mono"><AnimatedCounter value={overview?.total_products || 0} decimals={0} /></span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Total Stock</span>
              <span className="text-lg font-bold text-accent-cyan font-mono"><AnimatedCounter value={overview?.total_stock || 0} decimals={0} /></span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-muted">Low Stock Items</span>
              <span className={`text-lg font-bold font-mono ${(overview?.low_stock_alerts || 0) > 0 ? 'text-severity-critical' : 'text-severity-healthy'}`}>
                <AnimatedCounter value={overview?.low_stock_alerts || 0} decimals={0} />
              </span>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* ===== SECTION 5: FORECASTING CHARTS ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard delay={0.3}>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-severity-healthy" />
            <h2 className="text-sm font-semibold text-text-primary">Demand Forecast — Predicted vs Actual</h2>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={generateForecastData()}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={2} dot={false} name="AI Predicted" />
              <Line type="monotone" dataKey="actual" stroke="#06b6d4" strokeWidth={2} dot={false} name="Actual" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </GlassCard>

        <GlassCard delay={0.35}>
          <div className="flex items-center gap-2 mb-4">
            <Package size={18} className="text-accent-blue" />
            <h2 className="text-sm font-semibold text-text-primary">Inventory Health Trend</h2>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={generateInventoryTrend()}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="period" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <defs>
                <linearGradient id="stockGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="stockLevel" stroke="#3b82f6" fill="url(#stockGrad)" strokeWidth={2} name="Stock Level" />
              <Line type="monotone" dataKey="reorderPoint" stroke="#ef4444" strokeWidth={1} strokeDasharray="4 4" dot={false} name="Reorder Point" />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>

      {/* ===== SECTION 6: AUTONOMOUS ACTION TIMELINE ===== */}
      <GlassCard glowColor="purple" delay={0.4}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-accent-purple" />
            <h2 className="text-sm font-semibold text-text-primary">Autonomous Action Pipeline</h2>
          </div>
          <AIThinkingIndicator isActive={simState.is_running} size="sm" />
        </div>
        <TimelineStep steps={timelineSteps} />
      </GlassCard>

      {/* ===== SECTION 7: BASELINE VS AI COMPARISON ===== */}
      {improvements && Object.keys(improvements).length > 0 && (
        <GlassCard delay={0.45}>
          <div className="flex items-center gap-2 mb-4">
            <Shield size={18} className="text-accent-electric" />
            <h2 className="text-sm font-semibold text-text-primary">Baseline vs AI — Performance Gains</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'MAE Reduction', value: improvements.mae_reduction_pct, icon: TrendingDown, color: 'text-severity-healthy' },
              { label: 'Delay Reduction', value: improvements.delay_reduction_pct, icon: TrendingDown, color: 'text-severity-healthy' },
              { label: 'On-Time Improvement', value: improvements.on_time_improvement_pct, icon: TrendingUp, color: 'text-accent-blue' },
              { label: 'Stockout Reduction', value: improvements.stockout_reduction_pct, icon: TrendingDown, color: 'text-severity-healthy' },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                className="p-3 rounded-lg bg-bg-card text-center"
              >
                <item.icon size={20} className={`${item.color} mx-auto mb-1`} />
                <p className={`text-xl font-bold ${item.color}`}>
                  {item.label.includes('Improvement') ? '+' : '-'}{item.value || 0}%
                </p>
                <p className="text-[10px] text-text-muted mt-1">{item.label}</p>
              </motion.div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
};

// Helper: generate forecast data
function generateForecastData() {
  const periods = ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12'];
  let base = 120;
  return periods.map(p => {
    base += (Math.random() - 0.4) * 15;
    const predicted = Math.max(50, base);
    const actual = predicted + (Math.random() - 0.5) * 20;
    return { period: p, predicted: Math.round(predicted), actual: Math.round(actual) };
  });
}

// Helper: generate inventory trend
function generateInventoryTrend() {
  const periods = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14'];
  let stock = 450;
  return periods.map(p => {
    stock += (Math.random() - 0.5) * 60;
    stock = Math.max(100, Math.min(600, stock));
    return { period: p, stockLevel: Math.round(stock), reorderPoint: 200 };
  });
}

export default Dashboard;
