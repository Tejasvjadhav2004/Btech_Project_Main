import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Warehouse as WarehouseIcon, MapPin, Package, Gauge, AlertTriangle } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getWarehouses, getDashboardWarehouseStock } from '../services/api';

const Warehouses = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        // Try multiple API sources for warehouse data
        let data = null;
        try {
          const resp = await getWarehouses();
          data = Array.isArray(resp) ? resp : resp?.warehouses || resp?.data || [];
        } catch (e) {
          // Fallback to dashboard warehouse stock endpoint
          const resp = await getDashboardWarehouseStock();
          data = Array.isArray(resp) ? resp : resp?.warehouses || resp?.data || [];
        }
        setWarehouses(data || []);
      } catch (e) {
        console.error('Warehouses fetch error:', e);
        setError(e.message || 'Failed to load warehouses');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 skeleton rounded" />
        <LoadingSkeleton variant="card" count={6} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <AlertTriangle size={48} className="text-severity-critical mb-4" />
        <p className="text-severity-critical text-lg font-medium">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 rounded-lg bg-accent-blue/20 text-accent-blue hover:bg-accent-blue/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
          <WarehouseIcon size={24} className="text-accent-cyan" />
          Warehouse Network
        </h1>
        <p className="text-sm text-text-muted mt-1">Monitor warehouse capacity and operations</p>
      </div>

      {warehouses.length === 0 ? (
        <div className="text-center py-12">
          <WarehouseIcon size={48} className="text-text-dim mx-auto mb-4" />
          <p className="text-text-muted">No warehouses found</p>
          <p className="text-text-dim text-sm mt-1">Check if the backend API is running</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {warehouses.map((wh, i) => {
            const currentUtil = wh.current_utilization || wh.current_stock || 0;
            const capacity = wh.capacity || 1;
            const util = wh.utilization_rate || wh.utilization || Math.round((currentUtil / capacity) * 100);
            const status = util > 90 ? 'text-severity-critical' : util > 70 ? 'text-severity-high' : 'text-severity-healthy';
            return (
              <motion.div
                key={wh.warehouse_id || i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <GlassCard hover={true}>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-bold text-text-primary">{wh.warehouse_id || wh.name || `WH-${i}`}</h3>
                    <div className="flex items-center gap-1 text-xs text-text-muted">
                      <MapPin size={12} />
                      {wh.location?.city || wh.location || wh.city || '—'}
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-text-muted">Utilization</span>
                        <span className={`font-bold ${status}`}>
                          <AnimatedCounter value={util} />%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-bg-primary overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(util, 100)}%` }}
                          transition={{ duration: 1, delay: i * 0.1 }}
                          className={`h-full rounded-full ${util > 90 ? 'bg-severity-critical' : util > 70 ? 'bg-severity-high' : 'bg-severity-healthy'}`}
                        />
                      </div>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Capacity</span>
                      <span className="text-text-primary font-medium">{wh.capacity?.toLocaleString() || '—'}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Current Stock</span>
                      <span className="text-text-primary font-medium">{(wh.current_stock || wh.current_utilization || 0).toLocaleString()}</span>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Warehouses;
