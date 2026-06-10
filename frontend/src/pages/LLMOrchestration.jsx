import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, Brain, Loader, CheckCircle, Clock, Workflow, Zap } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import AIThinkingIndicator from '../components/ui/AIThinkingIndicator';
import AnimatedCounter from '../components/ui/AnimatedCounter';
import {
  getOrchestrationContext, generateOrchestrationPlan, executeOrchestrationPlan,
  getOrchestrationHistory, getOrchestrationMetrics, getOrchestrationHealth,
  runAutonomousPipeline, processSignalPipeline
} from '../services/api';

const LLMOrchestration = () => {
  const [health, setHealth] = useState(null);
  const [history, setHistory] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [h, hist, met] = await Promise.all([
          getOrchestrationHealth(), getOrchestrationHistory(15), getOrchestrationMetrics()
        ]);
        setHealth(h);
        setHistory(hist?.history || []);
        setMetrics(met?.metrics || null);
      } catch (e) {} finally { setLoading(false); }
    })();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try { await generateOrchestrationPlan({ dry_run: true }); }
    catch (e) {} finally { setGenerating(false); }
  };

  if (loading) return <LoadingSkeleton variant="card" count={4} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Bot size={24} className="text-accent-purple" /> LLM Orchestrator
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Large Language Model-powered autonomous decision engine
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge
            type={health?.status === 'healthy' ? 'healthy' : 'warning'}
            pulse={health?.status === 'healthy'} size="md"
          />
          <button onClick={handleGenerate} disabled={generating}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-purple/15 border border-accent-purple/25 text-accent-purple text-sm font-medium hover:bg-accent-purple/25 transition-all disabled:opacity-50">
            {generating ? <Loader size={14} className="animate-spin" /> : <Brain size={14} />}
            Generate Plan
          </button>
        </div>
      </div>

      {generating && <AIThinkingIndicator size="md" />}

      {/* Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { l: 'Total Decisions', v: metrics.total_decisions || 0, c: 'text-accent-blue' },
            { l: 'Pending', v: metrics.status_breakdown?.pending || 0, c: 'text-severity-high' },
            { l: 'Completed', v: metrics.status_breakdown?.completed || 0, c: 'text-severity-healthy' },
            { l: 'Failed', v: metrics.status_breakdown?.failed || 0, c: 'text-severity-critical' },
          ].map((m, i) => (
            <GlassCard key={i} delay={i * 0.05}>
              <p className="text-[10px] uppercase text-text-muted font-semibold">{m.l}</p>
              <p className={`text-2xl font-bold mt-1 ${m.c}`}>
                <AnimatedCounter value={m.v} decimals={0} />
              </p>
            </GlassCard>
          ))}
        </div>
      )}

      {/* History */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
          <Clock size={16} className="text-text-muted" /> Decision History
        </h3>
        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-12 text-text-muted text-sm">
              No LLM orchestration history yet
            </div>
          ) : (
            history.slice(0, 10).map((item, i) => (
              <motion.div key={item.id || i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}>
                <GlassCard padding="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <StatusBadge
                        type={item.status === 'success' ? 'success' : item.status === 'failed' ? 'critical' : 'info'}
                        size="xs"
                      />
                      <span className="text-xs font-mono text-text-muted">
                        {(item.decision_id || item.plan_id || item.id || '—').toString().slice(0, 16)}
                      </span>
                    </div>
                    <span className="text-[10px] text-text-dim font-mono">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary">
                    {item.summary || item.reasoning || item.description || 'LLM orchestration decision'}
                  </p>
                  {item.actions_count != null && (
                    <p className="text-[10px] text-text-dim mt-1">
                      {item.actions_count} actions • Confidence: {
                        item.confidence ? `${(item.confidence * 100).toFixed(0)}%` : 'N/A'
                      }
                    </p>
                  )}
                </GlassCard>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LLMOrchestration;
