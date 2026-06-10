import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain } from 'lucide-react';

const messages = [
  'Analyzing operational context...',
  'Generating optimization strategy...',
  'Executing autonomous workflow...',
  'Monitoring supply chain network...',
  'Processing demand signals...',
  'Evaluating inventory positions...',
  'Computing delivery routes...',
  'Synthesizing intelligence report...',
];

const AIThinkingIndicator = ({ isActive = true, size = 'md', className = '' }) => {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (!isActive) return;
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [isActive]);

  if (!isActive) return null;

  const sizeClasses = {
    sm: 'text-xs gap-2 px-3 py-1.5',
    md: 'text-sm gap-2.5 px-4 py-2',
    lg: 'text-base gap-3 px-5 py-3',
  };

  return (
    <motion.div
      className={`inline-flex items-center rounded-full bg-accent-purple/10 border border-accent-purple/20 ${sizeClasses[size]} ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
      >
        <Brain size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16} className="text-accent-purple" />
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.span
          key={messageIndex}
          className="text-accent-purple font-medium"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.3 }}
        >
          {messages[messageIndex]}
        </motion.span>
      </AnimatePresence>

      <div className="flex gap-0.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="w-1 h-1 rounded-full bg-accent-purple"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </div>
    </motion.div>
  );
};

export default AIThinkingIndicator;
