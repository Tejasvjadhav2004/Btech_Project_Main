import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({
  children,
  className = '',
  glowColor = null,
  hover = true,
  animate = true,
  delay = 0,
  padding = 'p-5',
  onClick = null,
  id = null,
}) => {
  const glowClasses = {
    blue: 'glow-blue',
    cyan: 'glow-cyan',
    purple: 'glow-purple',
    green: 'glow-green',
    red: 'glow-red',
    amber: 'glow-amber',
  };

  const baseClasses = `
    glass rounded-xl ${padding}
    ${hover ? 'glass-hover transition-all duration-300 cursor-default' : ''}
    ${glowColor ? glowClasses[glowColor] || '' : ''}
    ${onClick ? 'cursor-pointer' : ''}
    ${className}
  `.trim().replace(/\s+/g, ' ');

  if (animate) {
    return (
      <motion.div
        id={id}
        className={baseClasses}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay, ease: 'easeOut' }}
        whileHover={hover ? { scale: 1.01, y: -2 } : {}}
        onClick={onClick}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div id={id} className={baseClasses} onClick={onClick}>
      {children}
    </div>
  );
};

export default GlassCard;
