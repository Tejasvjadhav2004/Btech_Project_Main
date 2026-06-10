import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, CheckCircle, Bell } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getAlerts, acknowledgeSignal, resolveSignal } from '../services/api';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadAlerts = async () => { try { const d = await getAlerts(); setAlerts(Array.isArray(d) ? d : []); } catch (e) {} finally { setLoading(false); } };
  useEffect(() => { loadAlerts(); }, []);

  const handleAcknowledge = async (id) => { try { await acknowledgeSignal(id); await loadAlerts(); } catch (e) { alert(e.message); } };
  const handleResolve = async (id) => { try { await resolveSignal(id); await loadAlerts(); } catch (e) { alert(e.message); } };

  if (loading) return <LoadingSkeleton variant="card" count={4} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><AlertTriangle size={24} className="text-severity-high" /> Alerts & Signals</h1>
          <p className="text-sm text-text-muted mt-1">Active alerts requiring attention</p>
        </div>
        <span className="px-3 py-1 rounded-full bg-severity-high/15 text-severity-high text-xs font-semibold">{alerts.length} active</span>
      </div>
      <div className="space-y-3">
        {alerts.map((alert, i) => (
          <motion.div key={alert.signal_id || i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
            <GlassCard padding="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <StatusBadge type={alert.type?.toLowerCase() || 'warning'} pulse size="sm" />
                    <StatusBadge type={alert.severity?.toLowerCase() || 'medium'} size="xs" />
                  </div>
                  <p className="text-sm text-text-primary mb-1">{alert.message}</p>
                  <div className="flex items-center gap-4 text-[10px] text-text-dim">
                    <span>Entity: {alert.entity_id || '—'}</span>
                    <span>Product: {alert.product_id || '—'}</span>
                    <span className="font-mono">{alert.created_at ? new Date(alert.created_at).toLocaleString() : ''}</span>
                  </div>
                </div>
                <div className="flex gap-1.5 shrink-0">
                  <button onClick={() => handleAcknowledge(alert.signal_id)} className="px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-accent-blue hover:bg-accent-blue/10 border border-accent-blue/20 transition-colors">Acknowledge</button>
                  <button onClick={() => handleResolve(alert.signal_id)} className="px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-severity-healthy hover:bg-severity-healthy/10 border border-severity-healthy/20 transition-colors">Resolve</button>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        ))}
        {alerts.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-text-muted">
            <Shield size={40} className="opacity-20 mb-3" /><p className="text-sm">No active alerts — all clear</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;
