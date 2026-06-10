import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Package, Search, Filter, AlertTriangle, TrendingUp, ArrowUpDown } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getInventoryWithStock, getProductsList } from '../services/api';

const Inventory = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    (async () => {
      try {
        const data = await getInventoryWithStock();
        setInventory(Array.isArray(data) ? data : []);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const filtered = inventory.filter(item => {
    const matchSearch = !search || (item.sku || item.product_id || '').toLowerCase().includes(search.toLowerCase()) || (item.product_name || '').toLowerCase().includes(search.toLowerCase());
    if (filterStatus === 'low') return matchSearch && (item.quantity || 0) < (item.reorder_point || 20);
    if (filterStatus === 'out') return matchSearch && (item.quantity || 0) === 0;
    return matchSearch;
  });

  if (loading) return <div className="space-y-4"><LoadingSkeleton variant="table" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><Package size={24} className="text-accent-blue" /> Inventory Management</h1>
          <p className="text-sm text-text-muted mt-1">Real-time stock levels across all locations</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="px-2 py-1 rounded bg-bg-card">{inventory.length} items</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input type="text" placeholder="Search SKU or product..." value={search} onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-bg-card border border-glass-border text-sm text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent-blue/40 transition-colors" />
        </div>
        {['all', 'low', 'out'].map(f => (
          <button key={f} onClick={() => setFilterStatus(f)}
            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${filterStatus === f ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/25' : 'border border-glass-border text-text-muted hover:bg-glass-bg'}`}>
            {f === 'all' ? 'All' : f === 'low' ? 'Low Stock' : 'Out of Stock'}
          </button>
        ))}
      </div>

      {/* Table */}
      <GlassCard padding="p-0" hover={false}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-glass-border">
                {['SKU', 'Location', 'Quantity', 'Reorder Point', 'Status'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-[10px] uppercase tracking-wider text-text-muted font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 100).map((item, i) => {
                const qty = item.quantity || 0;
                const reorder = item.reorder_point || 20;
                const status = qty === 0 ? 'critical' : qty < reorder ? 'warning' : 'healthy';
                return (
                  <motion.tr key={item.id || i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.01 }}
                    className="border-b border-glass-border/50 hover:bg-bg-card-hover transition-colors">
                    <td className="px-4 py-3 text-xs font-mono text-accent-blue">{item.sku || item.product_id || '—'}</td>
                    <td className="px-4 py-3 text-xs text-text-muted">{item.warehouse_id || item.store_id || item.location_id || '—'}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-text-primary">{qty.toLocaleString()}</td>
                    <td className="px-4 py-3 text-xs text-text-muted">{reorder}</td>
                    <td className="px-4 py-3"><StatusBadge type={status} size="xs" /></td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <div className="text-center py-12 text-text-muted text-sm">No inventory items found</div>}
      </GlassCard>
    </div>
  );
};

export default Inventory;
