import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getAvailableRoles } from '../services/api';
import { BarChart3, Package, Store, Truck, Settings, User, Check, X } from 'lucide-react';

const RoleSelector = ({ onRoleSelect, onCancel, currentRole }) => {
  const roles = getAvailableRoles();

  const getRoleColor = (roleId) => {
    const colors = {
      'BUSINESS': { text: 'text-accent-blue', bg: 'bg-accent-blue', border: 'border-accent-blue' },
      'WAREHOUSE_MANAGER': { text: 'text-severity-high', bg: 'bg-severity-high', border: 'border-severity-high' },
      'STORE_MANAGER': { text: 'text-severity-healthy', bg: 'bg-severity-healthy', border: 'border-severity-healthy' },
      'LOGISTICS_MANAGER': { text: 'text-accent-purple', bg: 'bg-accent-purple', border: 'border-accent-purple' },
      'ADMIN': { text: 'text-severity-critical', bg: 'bg-severity-critical', border: 'border-severity-critical' },
    };
    return colors[roleId] || colors.BUSINESS;
  };

  const getRoleIcon = (roleId) => {
    const iconMap = {
      'BUSINESS': BarChart3,
      'WAREHOUSE_MANAGER': Package,
      'STORE_MANAGER': Store,
      'LOGISTICS_MANAGER': Truck,
      'ADMIN': Settings,
    };
    return iconMap[roleId] || User;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.3 }}
        className="relative glass rounded-2xl p-6 w-[480px] max-w-[90vw] border border-glass-border"
        style={{ background: 'rgba(15, 22, 41, 0.95)', backdropFilter: 'blur(24px)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-text-primary">Switch Role</h2>
            <p className="text-xs text-text-muted mt-0.5">Select a role to see its specialized view</p>
          </div>
          <button
            onClick={onCancel}
            className="p-2 rounded-lg hover:bg-glass-bg transition-colors text-text-muted hover:text-text-secondary"
          >
            <X size={18} />
          </button>
        </div>

        {/* Role Grid */}
        <div className="grid grid-cols-2 gap-3 mb-5">
          {roles.map((role) => {
            const colors = getRoleColor(role.id);
            const Icon = getRoleIcon(role.id);
            const isSelected = currentRole === role.id;

            return (
              <motion.button
                key={role.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onRoleSelect(role.id)}
                className={`relative flex flex-col items-center gap-2 p-4 rounded-xl border transition-all duration-200
                  ${isSelected
                    ? `${colors.border}/40 ${colors.bg}/10 border-2`
                    : 'border-glass-border hover:border-glass-hover bg-glass-bg hover:bg-glass-hover'
                  }
                `}
              >
                {isSelected && (
                  <div className={`absolute top-2 right-2 w-5 h-5 rounded-full ${colors.bg} flex items-center justify-center`}>
                    <Check size={12} className="text-white" strokeWidth={3} />
                  </div>
                )}
                <div className={`${colors.text} opacity-80`}>
                  <Icon size={24} strokeWidth={1.6} />
                </div>
                <span className={`text-sm font-medium ${isSelected ? colors.text : 'text-text-primary'}`}>
                  {role.name}
                </span>
                <span className="text-[10px] text-text-dim text-center leading-tight">
                  {role.description}
                </span>
              </motion.button>
            );
          })}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default RoleSelector;