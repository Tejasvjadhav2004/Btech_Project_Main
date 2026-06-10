import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Shield, Brain, Settings, ArrowRight } from 'lucide-react';
import GlassCard from './ui/GlassCard';
import AnimatedCounter from './ui/AnimatedCounter';
import { getDemoMetricsComparison } from '../services/api';

const DemoComparison = () => {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const d = await getDemoMetricsComparison(); setComparison(d); } catch (e) {}
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="flex justify-center py-12"><div className="skeleton w-full h-64 rounded-xl" /></div>;
  if (!comparison) return <div className="text-center py-12 text-text-muted">No comparison data available</div>;

  const baseline = comparison.baseline?.metrics || {};
  const ai = comparison.ai_autonomous?.metrics || {};
  const imp = comparison.improvements || {};

  const cards = [
    { title: 'MAE', baseline: baseline.mae, ai: ai.mae, imp: imp.mae_reduction_pct, unit: 'units', lower: true, desc: 'Forecast accuracy' },
    { title: 'RMSE', baseline: baseline.rmse, ai: ai.rmse, imp: imp.rmse_reduction_pct, unit: 'units', lower: true, desc: 'Error penalization' },
    { title: 'Avg Delay', baseline: baseline.avg_delivery_delay, ai: ai.avg_delivery_delay, imp: imp.delay_reduction_pct, unit: 'days', lower: true, desc: 'Delivery delay' },
    { title: 'On-Time %', baseline: baseline.on_time_delivery_pct, ai: ai.on_time_delivery_pct, imp: imp.on_time_improvement_pct, unit: '%', lower: false, desc: 'Delivery rate' },
    { title: 'Stock Util', baseline: baseline.stock_utilization_pct, ai: ai.stock_utilization_pct, imp: imp.utilization_improvement_pct, unit: '%', lower: false, desc: 'Space usage' },
    { title: 'Stock-Out', baseline: baseline.stock_out_rate_pct, ai: ai.stock_out_rate_pct, imp: imp.stockout_reduction_pct, unit: '%', lower: true, desc: 'Outage frequency' },
  ];

  return (
    <GlassCard padding="p-5" hover={false}>
      <div className="flex items-center gap-2 mb-5">
        <Shield size={20} className="text-accent-electric" />
        <h2 className="text-lg font-bold text-text-primary">Baseline vs AI Autonomous — Performance Comparison</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
        {cards.map((c, i) => {
          const better = c.lower ? (c.ai < c.baseline) : (c.ai > c.baseline);
          const color = better ? 'text-severity-healthy' : 'text-severity-critical';
          return (
            <motion.div key={i} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
              className="p-4 rounded-xl bg-bg-card border border-glass-border">
              <p className="text-xs text-text-muted mb-1">{c.title}</p>
              <p className="text-[10px] text-text-dim mb-3">{c.desc}</p>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="text-center p-2 rounded-lg bg-bg-primary">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Settings size={10} className="text-severity-high" />
                    <span className="text-[9px] text-severity-high font-medium">Baseline</span>
                  </div>
                  <p className="text-lg font-bold text-text-primary">
                    {typeof c.baseline === 'number' ? c.baseline.toFixed(1) : c.baseline || '—'}
                    <span className="text-[10px] text-text-dim ml-0.5">{c.unit}</span>
                  </p>
                </div>
                <div className="text-center p-2 rounded-lg bg-bg-primary">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Brain size={10} className="text-accent-purple" />
                    <span className="text-[9px] text-accent-purple font-medium">AI</span>
                  </div>
                  <p className={`text-lg font-bold ${color}`}>
                    {typeof c.ai === 'number' ? c.ai.toFixed(1) : c.ai || '—'}
                    <span className="text-[10px] text-text-dim ml-0.5">{c.unit}</span>
                  </p>
                </div>
              </div>
              <div className="flex justify-center">
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold ${better ? 'bg-severity-healthy/15 text-severity-healthy' : 'bg-severity-critical/15 text-severity-critical'}`}>
                  {c.lower ? <TrendingDown size={10} /> : <TrendingUp size={10} />}
                  {c.lower ? '-' : '+'}{c.imp || 0}% {c.lower ? 'Reduction' : 'Improvement'}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="p-4 rounded-xl bg-bg-card border border-glass-border">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
          {[
            { label: 'MAE Reduction', val: imp.mae_reduction_pct, icon: TrendingDown },
            { label: 'RMSE Reduction', val: imp.rmse_reduction_pct, icon: TrendingDown },
            { label: 'On-Time Gain', val: imp.on_time_improvement_pct, icon: TrendingUp, pos: true },
            { label: 'Response Time', val: imp.response_time_reduction_pct, icon: TrendingDown },
          ].map((s, i) => (
            <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-severity-healthy/8 border border-severity-healthy/15">
              <s.icon size={14} className="text-severity-healthy" />
              <span className="text-xs text-severity-healthy font-medium">{s.pos ? '+' : '-'}{s.val || 0}% {s.label}</span>
            </div>
          ))}
        </div>
        <p className="text-xs text-text-muted">{comparison.summary || 'AI system demonstrates significant improvements across all metrics.'}</p>
      </div>
    </GlassCard>
  );
};

export default DemoComparison;
