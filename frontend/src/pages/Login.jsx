import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, LogIn, User, Lock } from 'lucide-react';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onLogin) onLogin({ username, password });
  };

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-accent-blue/5 via-transparent to-accent-purple/5" />
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative glass rounded-2xl p-8 w-[400px] max-w-[90vw]">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center mb-4">
            <Brain size={28} className="text-white" />
          </div>
          <h1 className="text-xl font-bold text-text-primary">SupplyChain AI</h1>
          <p className="text-xs text-text-muted mt-1">Autonomous Command Center</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-lg bg-bg-card border border-glass-border text-sm text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent-blue/40" />
          </div>
          <div className="relative">
            <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-lg bg-bg-card border border-glass-border text-sm text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent-blue/40" />
          </div>
          <button type="submit"
            className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-gradient-to-r from-accent-blue to-accent-purple text-white font-semibold text-sm hover:opacity-90 transition-opacity">
            <LogIn size={16} /> Sign In
          </button>
        </form>
      </motion.div>
    </div>
  );
};

export default Login;
