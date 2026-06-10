import React from 'react';

const StatusBadge = ({ type, pulse = false, size = 'sm', className = '' }) => {
  const configs = {
    critical: { bg: 'bg-severity-critical/15', text: 'text-severity-critical', border: 'border-severity-critical/30', dot: 'bg-severity-critical' },
    high: { bg: 'bg-severity-high/15', text: 'text-severity-high', border: 'border-severity-high/30', dot: 'bg-severity-high' },
    warning: { bg: 'bg-severity-high/15', text: 'text-severity-high', border: 'border-severity-high/30', dot: 'bg-severity-high' },
    medium: { bg: 'bg-severity-medium/15', text: 'text-severity-medium', border: 'border-severity-medium/30', dot: 'bg-severity-medium' },
    healthy: { bg: 'bg-severity-healthy/15', text: 'text-severity-healthy', border: 'border-severity-healthy/30', dot: 'bg-severity-healthy' },
    success: { bg: 'bg-severity-healthy/15', text: 'text-severity-healthy', border: 'border-severity-healthy/30', dot: 'bg-severity-healthy' },
    info: { bg: 'bg-accent-blue/15', text: 'text-accent-blue', border: 'border-accent-blue/30', dot: 'bg-accent-blue' },
    ai: { bg: 'bg-accent-purple/15', text: 'text-accent-purple', border: 'border-accent-purple/30', dot: 'bg-accent-purple' },
    neutral: { bg: 'bg-text-muted/10', text: 'text-text-muted', border: 'border-text-muted/20', dot: 'bg-text-muted' },
    running: { bg: 'bg-severity-healthy/15', text: 'text-severity-healthy', border: 'border-severity-healthy/30', dot: 'bg-severity-healthy' },
    stopped: { bg: 'bg-severity-critical/15', text: 'text-severity-critical', border: 'border-severity-critical/30', dot: 'bg-severity-critical' },
    paused: { bg: 'bg-severity-high/15', text: 'text-severity-high', border: 'border-severity-high/30', dot: 'bg-severity-high' },
  };

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-[10px]',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-sm',
  };

  const c = configs[type] || configs.neutral;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium border ${c.bg} ${c.text} ${c.border} ${sizeClasses[size]} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot} ${pulse ? 'animate-pulse-glow' : ''}`} />
      {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
    </span>
  );
};

export default StatusBadge;
