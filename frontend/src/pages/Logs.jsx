import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getLogs } from '../services/api';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { (async () => { try { const d = await getLogs(); setLogs(Array.isArray(d) ? d : []); } catch (e) {} finally { setLoading(false); } })(); }, []);

  if (loading) return <LoadingSkeleton variant="table" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><FileText size={24} className="text-text-secondary" /> Logs & Anomalies</h1>
        <p className="text-sm text-text-muted mt-1">Execution logs and anomaly detection records</p>
      </div>
      <GlassCard padding="p-0" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr className="border-b border-glass-border">
              {['Timestamp', 'Type', 'Status', 'Details', 'Duration'].map(h => <th key={h} className="px-4 py-3 text-left text-[10px] uppercase tracking-wider text-text-muted font-semibold">{h}</th>)}
            </tr></thead>
            <tbody>
              {logs.slice(0, 100).map((log, i) => (
                <motion.tr key={log.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.01 }}
                  className="border-b border-glass-border/50 hover:bg-bg-card-hover transition-colors">
                  <td className="px-4 py-3 text-[10px] font-mono text-text-muted">{log.created_at || log.timestamp ? new Date(log.created_at || log.timestamp).toLocaleString() : '—'}</td>
                  <td className="px-4 py-3"><StatusBadge type={log.execution_type || log.type || 'info'} size="xs" /></td>
                  <td className="px-4 py-3"><StatusBadge type={log.status === 'success' || log.status === 'completed' ? 'success' : log.status === 'failed' ? 'critical' : 'info'} size="xs" /></td>
                  <td className="px-4 py-3 text-xs text-text-secondary max-w-md truncate">{log.details || log.message || log.description || '—'}</td>
                  <td className="px-4 py-3 text-[10px] text-text-dim font-mono">{log.duration_ms ? `${log.duration_ms}ms` : '—'}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
        {logs.length === 0 && <div className="text-center py-12 text-text-muted text-sm">No logs found</div>}
      </GlassCard>
    </div>
  );
};

export default Logs;
