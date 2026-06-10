import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import RoleSelector from './RoleSelector';
import AIThinkingIndicator from './ui/AIThinkingIndicator';
import { ChevronDown, Bell, Clock, Shield } from 'lucide-react';

const Layout = ({ children, activeTab, setActiveTab, selectedRole, onRoleSelect }) => {
  const [showRoleSelector, setShowRoleSelector] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const getRoleDisplayName = (role) => {
    const roleNames = {
      'BUSINESS': 'Business Owner',
      'WAREHOUSE_MANAGER': 'Warehouse Manager',
      'STORE_MANAGER': 'Store Manager',
      'LOGISTICS_MANAGER': 'Logistics Manager',
      'ADMIN': 'Administrator'
    };
    return roleNames[role] || role;
  };

  const getRoleColor = (role) => {
    const colors = {
      'BUSINESS': 'accent-blue',
      'WAREHOUSE_MANAGER': 'severity-high',
      'STORE_MANAGER': 'severity-healthy',
      'LOGISTICS_MANAGER': 'accent-purple',
      'ADMIN': 'severity-critical'
    };
    return colors[role] || 'accent-blue';
  };

  const roleColor = getRoleColor(selectedRole);

  return (
    <div className="flex min-h-screen bg-bg-primary">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} selectedRole={selectedRole} />

      {/* Main content area */}
      <div className="ml-[260px] flex-1 flex flex-col min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-30 h-14 bg-bg-primary/80 backdrop-blur-xl border-b border-glass-border flex items-center justify-between px-6">
          {/* Left: AI Status */}
          <div className="flex items-center gap-4">
            <AIThinkingIndicator size="sm" />
          </div>

          {/* Right: Role, Clock, Notifications */}
          <div className="flex items-center gap-3">
            {/* Live Clock */}
            <div className="flex items-center gap-1.5 text-xs text-text-muted font-mono">
              <Clock size={12} />
              <span>{currentTime.toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>

            <div className="w-px h-5 bg-glass-border" />

            {/* Notifications */}
            <button className="relative p-2 rounded-lg hover:bg-glass-bg transition-colors">
              <Bell size={16} className="text-text-secondary" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-severity-critical animate-pulse-glow" />
            </button>

            <div className="w-px h-5 bg-glass-border" />

            {/* Role Selector */}
            <button
              onClick={() => setShowRoleSelector(true)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-${roleColor}/10 border border-${roleColor}/20 hover:bg-${roleColor}/15 transition-all duration-200`}
            >
              <Shield size={14} className={`text-${roleColor}`} />
              <span className={`text-xs font-medium text-${roleColor}`}>
                {getRoleDisplayName(selectedRole)}
              </span>
              <ChevronDown size={12} className={`text-${roleColor} opacity-60`} />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Role Selector Modal */}
      <AnimatePresence>
        {showRoleSelector && (
          <RoleSelector
            onRoleSelect={(role) => {
              onRoleSelect(role);
              setShowRoleSelector(false);
            }}
            onCancel={() => setShowRoleSelector(false)}
            currentRole={selectedRole}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Layout;
