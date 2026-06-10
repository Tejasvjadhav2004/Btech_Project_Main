import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Brain, Package, ShoppingCart, Truck, Warehouse, Store,
  AlertTriangle, FileText, TrendingUp, Cpu, Workflow, Bot, Play,
  ChevronDown, ChevronRight, Zap, Radio, Activity, Settings
} from 'lucide-react';

const navGroups = {
  BUSINESS: [
    {
      id: 'command',
      label: 'Command Center',
      icon: Radio,
      items: [
        { id: 'dashboard', label: 'AI Dashboard', icon: LayoutDashboard },
        { id: 'demo', label: 'Live Simulation', icon: Play, highlight: true },
      ]
    },
    {
      id: 'intelligence',
      label: 'Intelligence',
      icon: Brain,
      items: [
        { id: 'intelligence', label: 'Signal Detection', icon: Zap },
        { id: 'predictive', label: 'Predictive AI', icon: TrendingUp },
      ]
    },
    {
      id: 'orchestration',
      label: 'Orchestration',
      icon: Workflow,
      items: [
        { id: 'orchestration', label: 'Workflow Engine', icon: Cpu },
      ]
    },
    {
      id: 'operations',
      label: 'Operations',
      icon: Package,
      items: [
        { id: 'inventory', label: 'Inventory', icon: Package },
        { id: 'orders', label: 'Orders', icon: ShoppingCart },
        { id: 'deliveries', label: 'Deliveries', icon: Truck },
        { id: 'warehouses', label: 'Warehouses', icon: Warehouse },
        { id: 'stores', label: 'Stores', icon: Store },
      ]
    },
    {
      id: 'system',
      label: 'System',
      icon: Settings,
      items: [
        { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
        { id: 'logs', label: 'Logs & Anomalies', icon: FileText },
      ]
    }
  ],
  WAREHOUSE_MANAGER: [
    {
      id: 'command', label: 'Command Center', icon: Radio,
      items: [
        { id: 'dashboard', label: 'AI Dashboard', icon: LayoutDashboard },
        { id: 'demo', label: 'Live Simulation', icon: Play, highlight: true },
      ]
    },
    {
      id: 'operations', label: 'Operations', icon: Package,
      items: [
        { id: 'inventory', label: 'Inventory', icon: Package },
        { id: 'warehouses', label: 'Warehouses', icon: Warehouse },
        { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
        { id: 'logs', label: 'Logs', icon: FileText },
      ]
    },
  ],
  STORE_MANAGER: [
    {
      id: 'command', label: 'Command Center', icon: Radio,
      items: [
        { id: 'dashboard', label: 'AI Dashboard', icon: LayoutDashboard },
        { id: 'demo', label: 'Live Simulation', icon: Play, highlight: true },
      ]
    },
    {
      id: 'operations', label: 'Operations', icon: Package,
      items: [
        { id: 'orders', label: 'Orders', icon: ShoppingCart },
        { id: 'deliveries', label: 'Deliveries', icon: Truck },
        { id: 'stores', label: 'Stores', icon: Store },
        { id: 'inventory', label: 'Inventory', icon: Package },
      ]
    },
  ],
  LOGISTICS_MANAGER: [
    {
      id: 'command', label: 'Command Center', icon: Radio,
      items: [
        { id: 'dashboard', label: 'AI Dashboard', icon: LayoutDashboard },
        { id: 'demo', label: 'Live Simulation', icon: Play, highlight: true },
      ]
    },
    {
      id: 'operations', label: 'Operations', icon: Package,
      items: [
        { id: 'deliveries', label: 'Deliveries', icon: Truck },
        { id: 'orders', label: 'Orders', icon: ShoppingCart },
        { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
        { id: 'warehouses', label: 'Warehouses', icon: Warehouse },
      ]
    },
  ],
  ADMIN: [
    {
      id: 'command', label: 'Command Center', icon: Radio,
      items: [
        { id: 'dashboard', label: 'AI Dashboard', icon: LayoutDashboard },
        { id: 'demo', label: 'Live Simulation', icon: Play, highlight: true },
      ]
    },
    {
      id: 'intelligence', label: 'Intelligence', icon: Brain,
      items: [
        { id: 'intelligence', label: 'Signal Detection', icon: Zap },
        { id: 'predictive', label: 'Predictive AI', icon: TrendingUp },
      ]
    },
    {
      id: 'orchestration', label: 'Orchestration', icon: Workflow,
      items: [
        { id: 'orchestration', label: 'Workflow Engine', icon: Cpu },
      ]
    },
    {
      id: 'operations', label: 'Operations', icon: Package,
      items: [
        { id: 'inventory', label: 'Inventory', icon: Package },
        { id: 'orders', label: 'Orders', icon: ShoppingCart },
        { id: 'deliveries', label: 'Deliveries', icon: Truck },
        { id: 'warehouses', label: 'Warehouses', icon: Warehouse },
        { id: 'stores', label: 'Stores', icon: Store },
      ]
    },
    {
      id: 'system', label: 'System', icon: Settings,
      items: [
        { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
        { id: 'logs', label: 'Logs & Anomalies', icon: FileText },
      ]
    }
  ],
};

const Sidebar = ({ activeTab, setActiveTab, selectedRole }) => {
  const groups = navGroups[selectedRole] || navGroups.BUSINESS;
  const [expandedGroups, setExpandedGroups] = useState(
    Object.fromEntries(groups.map(g => [g.id, true]))
  );

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  return (
    <div className="w-[260px] h-screen bg-bg-secondary/80 backdrop-blur-xl border-r border-glass-border flex flex-col fixed left-0 top-0 z-40">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-glass-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <Brain size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-text-primary tracking-tight">SupplyChain AI</h1>
            <p className="text-[10px] text-text-muted font-medium">Autonomous Command Center</p>
          </div>
        </div>
        {/* AI Status */}
        <div className="mt-3 flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-accent-purple/10 border border-accent-purple/20">
          <span className="status-dot status-dot-live bg-severity-healthy" />
          <span className="text-[10px] font-medium text-accent-purple">AI Engine Active</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {groups.map((group) => (
          <div key={group.id} className="mb-1">
            {/* Group header */}
            <button
              onClick={() => toggleGroup(group.id)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-text-muted hover:text-text-secondary hover:bg-glass-bg transition-colors duration-200"
            >
              <div className="flex items-center gap-2">
                <group.icon size={14} className="opacity-60" />
                <span className="text-[11px] font-semibold uppercase tracking-wider">{group.label}</span>
              </div>
              <motion.div animate={{ rotate: expandedGroups[group.id] ? 0 : -90 }} transition={{ duration: 0.2 }}>
                <ChevronDown size={12} />
              </motion.div>
            </button>

            {/* Group items */}
            <AnimatePresence>
              {expandedGroups[group.id] && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  {group.items.map((item) => {
                    const isActive = activeTab === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => setActiveTab(item.id)}
                        className={`w-full flex items-center gap-2.5 px-3 py-2 ml-2 mr-1 rounded-lg text-sm transition-all duration-200 relative group
                          ${isActive
                            ? item.highlight
                              ? 'bg-accent-purple/15 text-accent-purple border border-accent-purple/25'
                              : 'bg-accent-blue/12 text-accent-blue border border-accent-blue/20'
                            : item.highlight
                              ? 'text-accent-purple/70 hover:bg-accent-purple/8 hover:text-accent-purple border border-transparent'
                              : 'text-text-secondary hover:bg-glass-bg hover:text-text-primary border border-transparent'
                          }
                        `}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="activeTab"
                            className={`absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 rounded-r-full ${item.highlight ? 'bg-accent-purple' : 'bg-accent-blue'}`}
                            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                          />
                        )}
                        <item.icon size={16} className={`shrink-0 ${isActive ? '' : 'opacity-60 group-hover:opacity-100'}`} />
                        <span className="font-medium text-[13px]">{item.label}</span>
                        {item.highlight && (
                          <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-purple animate-pulse-glow" />
                        )}
                      </button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-glass-border">
        <div className="text-[10px] text-text-dim text-center">
          <span className="text-text-muted">v2.0</span> • AI Autonomous Engine
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
