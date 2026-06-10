import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Truck, Search, MapPin, Clock, Loader } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getDeliveries, startDelivery, completeDelivery } from '../services/api';

const Deliveries = () => {
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [actionLoading, setActionLoading] = useState(null);

  const loadData = async () => { try { const d = await getDeliveries(100, filter !== 'All' ? filter : null); setDeliveries(Array.isArray(d) ? d : []); } catch (e) {} finally { setLoading(false); } };
  useEffect(() => { loadData(); }, [filter]);

  const handleAction = async (fn, id) => { setActionLoading(id); try { await fn(id); await loadData(); } catch (e) { alert(e.message); } finally { setActionLoading(null); } };

  const statusMap = { pending: 'warning', in_transit: 'info', delivered: 'success', delayed: 'critical', cancelled: 'critical' };
  const statuses = ['All', 'Pending', 'In_Transit', 'Delivered', 'Delayed'];

  if (loading) return <LoadingSkeleton variant="table" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><Truck size={24} className="text-accent-purple" /> Delivery Tracking</h1>
        <p className="text-sm text-text-muted mt-1">Monitor and manage all deliveries in real-time</p>
      </div>
      <div className="flex items-center gap-3 flex-wrap">
        {statuses.map(s => (
          <button key={s} onClick={() => setFilter(s)} className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${filter === s ? 'bg-accent-purple/15 text-accent-purple border border-accent-purple/25' : 'border border-glass-border text-text-muted hover:bg-glass-bg'}`}>
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>
      <GlassCard padding="p-0" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr className="border-b border-glass-border">
              {['Delivery ID', 'Order', 'From', 'To', 'Transport', 'Duration', 'Status', 'ETA', 'Actions'].map(h => <th key={h} className="px-4 py-3 text-left text-[10px] uppercase tracking-wider text-text-muted font-semibold">{h}</th>)}
            </tr></thead>
            <tbody>
              {deliveries.slice(0, 50).map((d, i) => {
                const st = (d.status || 'pending').toLowerCase();
                const fromLocation = d.route?.find(r => r.action === 'pickup')?.city || d.warehouse_id || '—';
                const toLocation = d.route?.find(r => r.action === 'delivery')?.city || d.store_id || '—';
                const duration = d.estimated_duration_hours ? `${d.estimated_duration_hours.toFixed(1)}h` : '—';
                const transport = d.transport_mode || '—';
                const eta = d.estimated_arrival ? new Date(d.estimated_arrival) : null;
                const isDelayed = eta && eta < new Date() && st === 'in_transit';
                return (
                  <motion.tr key={d.delivery_id || d.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.01 }}
                    className="border-b border-glass-border/50 hover:bg-bg-card-hover transition-colors">
                    <td className="px-4 py-3 text-xs font-mono text-accent-purple">{(d.delivery_id || d.id || '').toString().slice(0, 12)}</td>
                    <td className="px-4 py-3 text-xs text-text-muted">{(d.order_id || '').toString().slice(0, 12)}</td>
                    <td className="px-4 py-3 text-xs text-text-secondary">{fromLocation}</td>
                    <td className="px-4 py-3 text-xs text-text-secondary">{toLocation}</td>
                    <td className="px-4 py-3 text-xs text-text-dim capitalize">{transport}</td>
                    <td className="px-4 py-3 text-xs text-text-dim">{duration}</td>
                    <td className="px-4 py-3"><StatusBadge type={statusMap[st] || 'neutral'} size="xs" /></td>
                    <td className={`px-4 py-3 text-[10px] font-mono ${isDelayed ? 'text-severity-critical' : 'text-text-dim'}`}>
                      {eta ? eta.toLocaleString() : '—'}
                      {isDelayed && <span className="ml-1">(Delayed)</span>}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {st === 'pending' && <button onClick={() => handleAction(startDelivery, d.delivery_id || d.id)} disabled={actionLoading === (d.delivery_id || d.id)} className="px-2 py-1 rounded text-[10px] font-medium text-accent-blue hover:bg-accent-blue/10 transition-colors disabled:opacity-50">{actionLoading === (d.delivery_id || d.id) ? <Loader size={10} className="animate-spin" /> : 'Start'}</button>}
                        {st === 'in_transit' && <button onClick={() => handleAction(completeDelivery, d.delivery_id || d.id)} disabled={actionLoading === (d.delivery_id || d.id)} className="px-2 py-1 rounded text-[10px] font-medium text-severity-healthy hover:bg-severity-healthy/10 transition-colors disabled:opacity-50">{actionLoading === (d.delivery_id || d.id) ? <Loader size={10} className="animate-spin" /> : 'Complete'}</button>}
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {deliveries.length === 0 && <div className="text-center py-12 text-text-muted text-sm">No deliveries found</div>}
      </GlassCard>
    </div>
  );
};

export default Deliveries;
