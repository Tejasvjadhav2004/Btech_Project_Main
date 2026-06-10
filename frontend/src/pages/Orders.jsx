import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ShoppingCart, Search, Filter, Package, Truck, CheckCircle, XCircle, Clock, Loader } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { fetchOrders, processOrder, shipOrder, deliverOrder, cancelOrder, getOrderStats } from '../services/api';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [actionLoading, setActionLoading] = useState(null);

  const loadData = async () => {
    try {
      const [o, s] = await Promise.all([fetchOrders(filter), getOrderStats()]);
      setOrders(Array.isArray(o) ? o : []);
      setStats(s);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, [filter]);

  const handleAction = async (fn, orderId) => {
    setActionLoading(orderId);
    try { await fn(orderId); await loadData(); } catch (e) { alert(e.message); }
    finally { setActionLoading(null); }
  };

  const statusColors = { pending: 'warning', processing: 'info', allocated: 'info', shipped: 'ai', delivered: 'success', cancelled: 'critical' };
  const statuses = ['All', 'Pending', 'Processing', 'Allocated', 'Shipped', 'Delivered', 'Cancelled'];

  const filtered = orders.filter(o => !search || (o.order_id || o.id || '').toString().includes(search) || (o.sku || '').toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div className="space-y-4"><LoadingSkeleton variant="table" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><ShoppingCart size={24} className="text-accent-blue" /> Order Management</h1>
        <p className="text-sm text-text-muted mt-1">Track and manage supply chain orders</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: 'Total', value: stats.total || orders.length, color: 'text-accent-blue' },
            { label: 'Pending', value: stats.pending || 0, color: 'text-severity-high' },
            { label: 'Processing', value: stats.processing || 0, color: 'text-accent-cyan' },
            { label: 'Shipped', value: stats.shipped || 0, color: 'text-accent-purple' },
            { label: 'Delivered', value: stats.delivered || 0, color: 'text-severity-healthy' },
          ].map((s, i) => (
            <div key={i} className="glass rounded-lg p-3 text-center">
              <p className="text-[10px] uppercase text-text-muted font-semibold">{s.label}</p>
              <p className={`text-xl font-bold ${s.color} mt-1`}>{s.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input type="text" placeholder="Search orders..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-bg-card border border-glass-border text-sm text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent-blue/40" />
        </div>
        {statuses.map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${filter === s ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/25' : 'border border-glass-border text-text-muted hover:bg-glass-bg'}`}>
            {s}
          </button>
        ))}
      </div>

      {/* Table */}
      <GlassCard padding="p-0" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-glass-border">
                {['Order ID', 'SKU', 'Store', 'Qty', 'Warehouse', 'Priority', 'Status', 'ETA', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] uppercase tracking-wider text-text-muted font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map((order, i) => {
                const st = (order.status || 'pending').toLowerCase();
                const storeName = order.allocation_details?.warehouse_decision?.store?.city || order.store_id || '—';
                const warehouseName = order.assigned_warehouse || order.warehouse_id || '—';
                const sku = order.sku || order.items?.[0]?.sku || '—';
                const quantity = order.quantity || order.items?.[0]?.quantity || 0;
                const expectedDelivery = order.expected_delivery || order.allocation_details?.warehouse_decision?.expected_delivery;
                return (
                  <motion.tr key={order.order_id || order.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.01 }}
                    className="border-b border-glass-border/50 hover:bg-bg-card-hover transition-colors">
                    <td className="px-4 py-3 text-xs font-mono text-accent-blue">{(order.order_id || order.id || '').toString().slice(0, 12)}</td>
                    <td className="px-4 py-3 text-sm text-text-primary">{sku}</td>
                    <td className="px-4 py-3 text-xs text-text-muted">{storeName}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-text-primary">{quantity}</td>
                    <td className="px-4 py-3 text-xs text-text-secondary">{warehouseName}</td>
                    <td className="px-4 py-3"><StatusBadge type={order.priority === 'urgent' || order.priority === 'high' ? 'critical' : order.priority === 'normal' ? 'warning' : 'info'} size="xs" label={order.priority || 'normal'} /></td>
                    <td className="px-4 py-3"><StatusBadge type={statusColors[st] || 'neutral'} size="xs" /></td>
                    <td className="px-4 py-3 text-[10px] text-text-dim font-mono">{expectedDelivery ? new Date(expectedDelivery).toLocaleString() : '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {st === 'pending' && <ActionBtn label="Process" onClick={() => handleAction(processOrder, order.order_id || order.id)} loading={actionLoading === (order.order_id || order.id)} />}
                        {st === 'processing' && <ActionBtn label="Ship" onClick={() => handleAction(shipOrder, order.order_id || order.id)} loading={actionLoading === (order.order_id || order.id)} />}
                        {st === 'shipped' && <ActionBtn label="Deliver" onClick={() => handleAction(deliverOrder, order.order_id || order.id)} loading={actionLoading === (order.order_id || order.id)} />}
                        {(st === 'pending' || st === 'processing') && <ActionBtn label="Cancel" color="critical" onClick={() => handleAction(cancelOrder, order.order_id || order.id)} loading={actionLoading === (order.order_id || order.id)} />}
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <div className="text-center py-12 text-text-muted text-sm">No orders found</div>}
      </GlassCard>
    </div>
  );
};

const ActionBtn = ({ label, onClick, loading, color = 'blue' }) => {
  const colors = { blue: 'text-accent-blue hover:bg-accent-blue/10', critical: 'text-severity-critical hover:bg-severity-critical/10' };
  return (
    <button onClick={onClick} disabled={loading}
      className={`px-2 py-1 rounded text-[10px] font-medium ${colors[color]} transition-colors disabled:opacity-50`}>
      {loading ? <Loader size={10} className="animate-spin" /> : label}
    </button>
  );
};

export default Orders;
