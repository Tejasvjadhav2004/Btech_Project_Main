import React from 'react';
import { motion } from 'framer-motion';
import AnimatedCounter from './AnimatedCounter';
import {
  TrendingUp, TrendingDown, Minus
} from 'lucide-react';

const KPICard = ({
  title,
  value,
  unit = '',
  trend = null,       // 'up' | 'down' | 'neutral'
  trendValue = '',     // e.g. "+12%"
  status = 'neutral',  // 'good' | 'warning' | 'critical' | 'neutral'
  icon = null,
  sparklineData = null,
  delay = 0,
  decimals = 1,
  target = null,
}) => {
  const statusColors = {
    good: { bg: 'bg-severity-healthy/10', text: 'text-severity-healthy', border: 'border-severity-healthy/20', glow: 'glow-green' },
    warning: { bg: 'bg-severity-high/10', text: 'text-severity-high', border: 'border-severity-high/20', glow: 'glow-amber' },
    critical: { bg: 'bg-severity-critical/10', text: 'text-severity-critical', border: 'border-severity-critical/20', glow: 'glow-red' },
    neutral: { bg: 'bg-accent-blue/10', text: 'text-accent-blue', border: 'border-accent-blue/20', glow: 'glow-blue' },
  };

  const trendIcons = {
    up: <TrendingUp size={14} />,
    down: <TrendingDown size={14} />,
    neutral: <Minus size={14} />,
  };

  const trendColors = {
    up: 'text-severity-healthy',
    down: 'text-severity-critical',
    neutral: 'text-text-muted',
  };

  const sc = statusColors[status] || statusColors.neutral;

  return (
    <motion.div
      className={`glass rounded-xl p-5 relative overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:-translate-y-0.5 ${sc.glow}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: 'easeOut' }}
    >
      {/* Status top bar */}
      <div className={`absolute top-0 left-0 right-0 h-[2px] ${sc.bg}`}>
        <div className={`h-full ${sc.text} bg-current`} style={{ width: '100%', opacity: 0.6 }} />
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {icon && <div className={`${sc.text} opacity-70`}>{icon}</div>}
          <span className="text-xs font-medium text-text-secondary uppercase tracking-wider">{title}</span>
        </div>
        {trend && trendValue && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trendColors[trend]}`}>
            {trendIcons[trend]}
            <span>{trendValue}</span>
          </div>
        )}
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2">
        <span className={`text-3xl font-bold ${sc.text}`}>
          <AnimatedCounter value={value} decimals={decimals} />
        </span>
        {unit && <span className="text-sm text-text-muted">{unit}</span>}
      </div>

      {/* Target */}
      {target && (
        <div className="mt-1.5 text-[10px] text-text-dim">
          Target: <span className="text-text-muted">{target}</span>
        </div>
      )}

      {/* Mini Sparkline */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-4 h-10">
          <MiniSparkline data={sparklineData} color={sc.text} />
        </div>
      )}
    </motion.div>
  );
};

const MiniSparkline = ({ data, color }) => {
  const width = 120;
  const height = 28;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`spark-${data.length}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.3" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className={color}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#spark-${data.length})`}
        className={color}
      />
    </svg>
  );
};

export default KPICard;
