import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Activity, RefreshCw } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { getForecast } from '../services/api';

const DarkTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-lg px-3 py-2 text-xs" style={{ background: 'rgba(15,22,41,0.95)', border: '1px solid rgba(255,255,255,0.08)' }}>
      <p className="text-text-muted mb-1">{label}</p>
      {payload.map((p, i) => (<p key={i} style={{ color: p.color }} className="font-medium">{p.name}: {p.value}</p>))}
    </div>
  );
};

const Forecast = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { (async () => { try { const d = await getForecast(); setData(Array.isArray(d) ? d : []); } catch (e) {} finally { setLoading(false); } })(); }, []);

  if (loading) return <LoadingSkeleton variant="chart" count={2} />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2"><TrendingUp size={24} className="text-severity-healthy" /> Demand Forecasting</h1>
        <p className="text-sm text-text-muted mt-1">AI-powered demand prediction and trend analysis</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><Activity size={16} className="text-accent-purple" /> Predicted vs Actual</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6', r: 3 }} name="Predicted" />
              <Line type="monotone" dataKey="actual" stroke="#06b6d4" strokeWidth={2} dot={{ fill: '#06b6d4', r: 3 }} name="Actual" />
            </LineChart>
          </ResponsiveContainer>
        </GlassCard>
        <GlassCard>
          <h3 className="text-sm font-semibold text-text-primary mb-4 flex items-center gap-2"><TrendingUp size={16} className="text-accent-cyan" /> Demand Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<DarkTooltip />} />
              <defs>
                <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} /><stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="predicted" stroke="#8b5cf6" fill="url(#forecastGrad)" strokeWidth={2} name="Forecast" />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>
    </div>
  );
};

export default Forecast;
