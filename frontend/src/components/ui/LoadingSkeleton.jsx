import React from 'react';

const LoadingSkeleton = ({ variant = 'card', count = 1, className = '' }) => {
  const variants = {
    card: (i) => (
      <div key={i} className={`skeleton h-32 rounded-xl ${className}`} />
    ),
    kpi: (i) => (
      <div key={i} className="skeleton h-28 rounded-xl" />
    ),
    chart: (i) => (
      <div key={i} className={`skeleton h-64 rounded-xl ${className}`} />
    ),
    feed: (i) => (
      <div key={i} className="flex gap-3 mb-3">
        <div className="skeleton w-8 h-8 rounded-full shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="skeleton h-4 w-3/4 rounded" />
          <div className="skeleton h-3 w-1/2 rounded" />
        </div>
      </div>
    ),
    table: (i) => (
      <div key={i} className="space-y-2">
        <div className="skeleton h-10 rounded-lg" />
        {Array.from({ length: 5 }).map((_, j) => (
          <div key={j} className="skeleton h-12 rounded-lg" />
        ))}
      </div>
    ),
    text: (i) => (
      <div key={i} className="space-y-2">
        <div className="skeleton h-4 w-full rounded" />
        <div className="skeleton h-4 w-5/6 rounded" />
        <div className="skeleton h-4 w-2/3 rounded" />
      </div>
    ),
  };

  const renderer = variants[variant] || variants.card;

  return (
    <div className={variant === 'kpi' ? 'grid grid-cols-2 lg:grid-cols-4 gap-4' : ''}>
      {Array.from({ length: count }).map((_, i) => renderer(i))}
    </div>
  );
};

export default LoadingSkeleton;
