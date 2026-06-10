import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, Play, Square, Radar, Radio, Shield, RefreshCw, AlertTriangle, CheckCircle, Sparkles } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import { getSignalStats, getActiveSignals, getSchedulerStatus, runAllDetections, startScheduler, stopScheduler, runDetection, acknowledgeSignal, resolveSignal, generateDemoSignals } from '../services/api';

const Intelligence = () => {
  const [stats, setStats] = useState(null);
  const [signals, setSignals] = useState([]);
  const [scheduler, setScheduler] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const loadData = async () => {
    try { const [s, sig, sch] = await Promise.all([getSignalStats(), getActiveSignals(), getSchedulerStatus()]); setStats(s); setSignals(sig?.signals || []); setScheduler(sch); } catch (e) {} finally { setLoading(false); }
  };
  useEffect(() => { loadData(); const iv = setInterval(loadData, 30000); return () => clearInterval(iv); }, []);

  const handleRunAll = async () => { setRunning(true); try { await runAllDetections(); await loadData(); } catch (e) {} finally { setRunning(false); } };
  const handleStartSch = async () => { try { await startScheduler(); await loadData(); } catch (e) {} };
  const handleStopSch = async () => { try { await stopScheduler(); await loadData(); } catch (e) {} };
  const handleGenerateDemo = async () => { setRunning(true); try { await generateDemoSignals(25); await loadData(); } catch (e) {} finally { setRunning(false); } };

  if (loading) return <div className="space-y-4"><LoadingSkeleton variant="kpi" count={4} /><LoadingSkeleton variant="card" count={3} /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><Zap size={24} className="text-severity-high" /> Signal Intelligence</h1>
          <p className="text-sm text-text-muted mt-1">AI-powered anomaly detection and signal processing</p>
        </div>
        <button onClick={handleRunAll} disabled={running}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-blue/15 border border-accent-blue/25 text-accent-blue text-sm font-medium hover:bg-accent-blue/25 transition-all disabled:opacity-50">
          <Radar size={16} className={running ? 'animate-spin' : ''} />{running ? 'Running...' : 'Run All Detections'}
        </button>
        <button onClick={handleGenerateDemo} disabled={running}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-purple/15 border border-accent-purple/25 text-accent-purple text-sm font-medium hover:bg-accent-purple/25 transition-all disabled:opacity-50">
          <Sparkles size={16} />Generate Demo Data
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Signals', value: stats?.total_signals || 0, color: 'text-accent-blue' },
          { label: 'Active', value: signals.length, color: 'text-severity-high' },
          { label: 'Resolved', value: stats?.resolved_count || 0, color: 'text-severity-healthy' },
          { label: 'Detection Rate', value: stats?.detection_rate || 0, color: 'text-accent-purple', suffix: '%' },
        ].map((s, i) => (
          <GlassCard key={i} delay={i * 0.05}>
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-semibold">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}><AnimatedCounter value={s.value} decimals={s.suffix ? 1 : 0} suffix={s.suffix || ''} /></p>
          </GlassCard>
        ))}
      </div>

      {/* Scheduler */}
      <GlassCard padding="p-4" hover={false}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2"><Radio size={16} className="text-accent-cyan" /> Scheduler</h3>
          <StatusBadge type={scheduler?.status === 'running' ? 'running' : 'stopped'} pulse={scheduler?.status === 'running'} size="sm" />
        </div>
        <div className="flex gap-2">
          <button onClick={handleStartSch} disabled={scheduler?.status === 'running'} className="px-3 py-1.5 rounded-lg text-xs font-medium text-severity-healthy border border-severity-healthy/20 hover:bg-severity-healthy/10 transition-colors disabled:opacity-30"><Play size={12} className="inline mr-1" />Start</button>
          <button onClick={handleStopSch} disabled={scheduler?.status !== 'running'} className="px-3 py-1.5 rounded-lg text-xs font-medium text-severity-critical border border-severity-critical/20 hover:bg-severity-critical/10 transition-colors disabled:opacity-30"><Square size={12} className="inline mr-1" />Stop</button>
        </div>
      </GlassCard>

      {/* Signal Distribution */}
      {stats?.by_type && (
        <GlassCard padding="p-4" hover={false}>
          <h3 className="text-sm font-semibold text-text-primary mb-3">Signal Distribution</h3>
          <div className="space-y-2">
            {Object.entries(stats.by_type).map(([type, count]) => (
              <div key={type} className="flex items-center gap-3">
                <span className="text-xs text-text-muted w-32 truncate">{type.replace(/_/g, ' ')}</span>
                <div className="flex-1 h-2 rounded-full bg-bg-primary overflow-hidden">
                  <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min((count / (stats.total_signals || 1)) * 100, 100)}%` }} transition={{ duration: 0.8 }}
                    className="h-full rounded-full bg-accent-blue" />
                </div>
                <span className="text-xs text-text-primary font-mono w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Active Signals */}
      {signals.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2"><AlertTriangle size={16} className="text-severity-high" /> Active Signals ({signals.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {signals.map((sig, i) => (
              <motion.div key={sig.signal_id || i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <GlassCard padding="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <StatusBadge type={sig.type?.toLowerCase() || 'info'} pulse size="xs" />
                    <StatusBadge type={sig.severity?.toLowerCase() || 'medium'} size="xs" />
                  </div>
                  <p className="text-sm text-text-primary mb-2">{sig.message}</p>
                  <div className="text-[10px] text-text-dim space-y-0.5">
                    <p>Entity: {sig.entity_id} | Product: {sig.product_id || 'N/A'}</p>
                    <p className="font-mono">{sig.created_at ? new Date(sig.created_at).toLocaleString() : ''}</p>
                  </div>
                  <div className="flex gap-1.5 mt-3">
                    <button onClick={() => acknowledgeSignal(sig.signal_id).then(loadData)} className="px-2 py-1 rounded text-[10px] font-medium text-accent-blue hover:bg-accent-blue/10 border border-accent-blue/20">Acknowledge</button>
                    <button onClick={() => resolveSignal(sig.signal_id).then(loadData)} className="px-2 py-1 rounded text-[10px] font-medium text-severity-healthy hover:bg-severity-healthy/10 border border-severity-healthy/20">Resolve</button>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Intelligence;
