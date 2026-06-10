import React from 'react';
import { motion } from 'framer-motion';
import { Check, Loader, Circle } from 'lucide-react';

const TimelineStep = ({ steps = [], className = '' }) => {
  const statusConfig = {
    completed: { icon: Check, color: 'text-severity-healthy', bg: 'bg-severity-healthy', line: 'bg-severity-healthy' },
    active: { icon: Loader, color: 'text-accent-purple', bg: 'bg-accent-purple', line: 'bg-accent-purple' },
    pending: { icon: Circle, color: 'text-text-dim', bg: 'bg-text-dim', line: 'bg-bg-elevated' },
  };

  return (
    <div className={`flex items-start gap-0 overflow-x-auto pb-2 ${className}`}>
      {steps.map((step, index) => {
        const config = statusConfig[step.status] || statusConfig.pending;
        const Icon = config.icon;
        const isLast = index === steps.length - 1;

        return (
          <motion.div
            key={index}
            className="flex items-center shrink-0"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
          >
            {/* Step node */}
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                step.status === 'completed' ? 'border-severity-healthy bg-severity-healthy/20' :
                step.status === 'active' ? 'border-accent-purple bg-accent-purple/20 animate-border-glow' :
                'border-text-dim/30 bg-bg-card'
              }`}>
                <Icon size={14} className={`${config.color} ${step.status === 'active' ? 'animate-spin' : ''}`} />
              </div>
              <span className={`mt-1.5 text-[10px] font-medium ${config.color} max-w-[70px] text-center leading-tight`}>
                {step.label}
              </span>
              {step.duration && (
                <span className="text-[9px] text-text-dim mt-0.5">{step.duration}</span>
              )}
            </div>

            {/* Connector line */}
            {!isLast && (
              <div className={`w-8 h-0.5 mt-[-12px] mx-1 ${
                step.status === 'completed' ? config.line : 'bg-bg-elevated'
              } rounded-full`} />
            )}
          </motion.div>
        );
      })}
    </div>
  );
};

export default TimelineStep;
