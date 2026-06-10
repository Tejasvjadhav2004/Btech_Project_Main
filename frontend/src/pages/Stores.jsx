import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Store as StoreIcon, MapPin, ShoppingCart, Package, AlertTriangle } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getStores } from '../services/api';

const Stores = () => {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const d = await getStores();
        setStores(Array.isArray(d) ? d : []);
      } catch (e) {
        console.error('Stores fetch error:', e);
        setError(e.message || 'Failed to load stores');
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
          <StoreIcon size={24} className="text-severity-healthy" />
          Store Network
        </h1>
        <p className="text-sm text-text-muted mt-1">Monitor retail store operations and inventory</p>
      </div>

      {stores.length === 0 ? (
        <div className="text-center py-12">
          <StoreIcon size={48} className="text-text-dim mx-auto mb-4" />
          <p className="text-text-muted">No stores found</p>
          <p className="text-text-dim text-sm mt-1">Check if the backend API is running</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stores.map((store, i) => (
            <motion.div
              key={store.store_id || i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <GlassCard hover={true}>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-text-primary">{store.name || store.store_id || `Store-${i}`}</h3>
                  <div className="flex items-center gap-1 text-xs text-text-muted">
                    <MapPin size={12} />{store.location?.city || store.city || '—'}
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">Capacity</span>
                    <span className="text-text-primary">{store.capacity?.toLocaleString() || '—'} units</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">Utilization</span>
                    <span className={store.current_utilization > store.capacity * 0.9 ? 'text-severity-critical font-medium' : store.current_utilization > store.capacity * 0.7 ? 'text-severity-high font-medium' : 'text-severity-healthy font-medium'}>
                      {store.current_utilization?.toLocaleString() || 0} units ({store.capacity ? Math.round((store.current_utilization / store.capacity) * 100) : 0}%)
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted">Status</span>
                    <span className={store.is_active ? 'text-severity-healthy font-medium' : 'text-severity-critical font-medium'}>
                      {store.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Stores;
