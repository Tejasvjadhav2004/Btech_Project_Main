import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Brain, AlertTriangle, Loader, Zap, Activity, Shield } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import { getDemandPredictions, getStockoutRisks, getDelayRisks, getModelStatus, trainDemandModel, generateDemandPredictions, runPredictiveSensing, getHighDemandItems } from '../services/api';

const PredictiveIntelligence = () => {
  const [predictions, setPredictions] = useState([]);
  const [stockoutRisks, setStockoutRisks] = useState([]);
  const [delayRisks, setDelayRisks] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [highDemand, setHighDemand] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [pred, sr, dr, ms, hd] = await Promise.all([getDemandPredictions(null, null, 20), getStockoutRisks(null, 20), getDelayRisks(null, 20), getModelStatus(), getHighDemandItems()]);
        setPredictions(Array.isArray(pred) ? pred : []);
        setStockoutRisks(Array.isArray(sr) ? sr : []);
        setDelayRisks(Array.isArray(dr) ? dr : []);
        setModelStatus(ms);
        setHighDemand(Array.isArray(hd) ? hd : []);
      } catch (e) {} finally { setLoading(false); }
    })();
  }, []);

  const handleAction = async (fn, key) => {
    setActionLoading(key);
    try { await fn(); } catch (e) { alert(e.message); }
    finally { setActionLoading(null); }
  };

  if (loading) return <div className="space-y-4"><LoadingSkeleton variant="kpi" count={4} /><LoadingSkeleton variant="table" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><Brain size={24} className="text-accent-purple" /> Predictive Intelligence</h1>
          <p className="text-sm text-text-muted mt-1">AI-powered risk assessment and demand prediction</p>
        </div>
        <div className="flex gap-2">
          {[
            { label: 'Train Model', fn: trainDemandModel, key: 'train' },
            { label: 'Generate Predictions', fn: generateDemandPredictions, key: 'gen' },
            { label: 'Run Sensing', fn: runPredictiveSensing, key: 'sense' },
          ].map(a => (
            <button key={a.key} onClick={() => handleAction(a.fn, a.key)} disabled={actionLoading === a.key}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-accent-purple border border-accent-purple/20 hover:bg-accent-purple/10 transition-colors disabled:opacity-50">
              {actionLoading === a.key ? <Loader size={12} className="animate-spin inline mr-1" /> : null}{a.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard delay={0}><p className="text-[10px] uppercase text-text-muted font-semibold">Predictions</p><p className="text-2xl font-bold text-accent-blue mt-1"><AnimatedCounter value={predictions.length} decimals={0} /></p></GlassCard>
        <GlassCard delay={0.05}><p className="text-[10px] uppercase text-text-muted font-semibold">Stockout Risks</p><p className="text-2xl font-bold text-severity-critical mt-1"><AnimatedCounter value={stockoutRisks.length} decimals={0} /></p></GlassCard>
        <GlassCard delay={0.1}><p className="text-[10px] uppercase text-text-muted font-semibold">Delay Risks</p><p className="text-2xl font-bold text-severity-high mt-1"><AnimatedCounter value={delayRisks.length} decimals={0} /></p></GlassCard>
        <GlassCard delay={0.15}><p className="text-[10px] uppercase text-text-muted font-semibold">High Demand</p><p className="text-2xl font-bold text-accent-purple mt-1"><AnimatedCounter value={highDemand.length} decimals={0} /></p></GlassCard>
      </div>

      {/* Model Status */}
      {modelStatus && (
        <GlassCard padding="p-4" hover={false}>
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2"><Activity size={16} className="text-accent-cyan" /> Model Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
            <div><span className="text-text-muted">Status:</span> <span className="text-severity-healthy font-medium">{modelStatus.demand_forecast_model?.exists ? 'Ready' : 'Not Available'}</span></div>
            <div><span className="text-text-muted">Algorithm:</span> <span className="text-text-primary uppercase">{modelStatus.demand_forecast_model?.metadata?.model_type || 'N/A'}</span></div>
            <div><span className="text-text-muted">R² Score:</span> <span className="text-accent-purple font-medium">{modelStatus.demand_forecast_model?.metadata?.metrics?.R2 ? `${(modelStatus.demand_forecast_model.metadata.metrics.R2 * 100).toFixed(1)}%` : 'N/A'}</span></div>
            <div><span className="text-text-muted">RMSE:</span> <span className="text-text-primary">{modelStatus.demand_forecast_model?.metadata?.metrics?.RMSE?.toFixed(2) || 'N/A'}</span></div>
            <div><span className="text-text-muted">Last Trained:</span> <span className="text-text-primary font-mono">{modelStatus.demand_forecast_model?.metadata?.training_date ? new Date(modelStatus.demand_forecast_model.metadata.training_date).toLocaleDateString() : 'N/A'}</span></div>
          </div>
        </GlassCard>
      )}

      {/* Stockout Risks */}
      {stockoutRisks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2"><AlertTriangle size={16} className="text-severity-critical" /> Stockout Risks</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {stockoutRisks.slice(0, 9).map((risk, i) => (
              <GlassCard key={i} padding="p-3" delay={i * 0.03}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-accent-blue">{risk.sku || risk.product_id}</span>
                  <StatusBadge type={risk.severity?.toLowerCase() || 'critical'} size="xs" />
                </div>
                <p className="text-xs text-text-secondary">{risk.message || risk.description || 'Stock-out risk detected'}</p>
                <div className="text-[10px] text-text-dim mt-2">{risk.store_id || risk.location || ''}</div>
              </GlassCard>
            ))}
          </div>
        </div>
      )}

      {/* Delay Risks */}
      {delayRisks.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2"><Zap size={16} className="text-severity-high" /> Delay Risks</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {delayRisks.slice(0, 9).map((risk, i) => (
              <GlassCard key={i} padding="p-3" delay={i * 0.03}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-accent-purple">{risk.delivery_id || risk.order_id || 'Order'}</span>
                  <StatusBadge type={risk.severity?.toLowerCase() || 'warning'} size="xs" />
                </div>
                <p className="text-xs text-text-secondary">{risk.message || risk.description || 'Delay risk detected'}</p>
              </GlassCard>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictiveIntelligence;
