import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import RoleSelector from './RoleSelector';

const Layout = ({ children, activeTab, setActiveTab, selectedRole, onRoleSelect }) => {
  const [showRoleSelector, setShowRoleSelector] = useState(false);
  const [roleChanged, setRoleChanged] = useState(false);

  // Debug log when selectedRole changes
  useEffect(() => {
    console.log('=== ROLE CHANGED ===');
    console.log('New role:', selectedRole);
    console.log('Dashboard should show:', getDashboardName(selectedRole));
    setRoleChanged(true);
    const timer = setTimeout(() => setRoleChanged(false), 1000);
    return () => clearTimeout(timer);
  }, [selectedRole]);

  const handleRoleClick = () => {
    setShowRoleSelector(true);
  };

  const handleRoleSelect = (role) => {
    console.log('Role selected in Layout:', role);
    onRoleSelect(role);
    setShowRoleSelector(false);
  };

  const handleCancelRoleSelect = () => {
    setShowRoleSelector(false);
  };

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
      'BUSINESS': '#3b82f6',      // Blue
      'WAREHOUSE_MANAGER': '#f59e0b', // Amber
      'STORE_MANAGER': '#10b981',    // Green
      'LOGISTICS_MANAGER': '#8b5cf6', // Purple
      'ADMIN': '#ef4444'             // Red
    };
    return colors[role] || '#3b82f6';
  };

  const getDashboardName = (role) => {
    const names = {
      'BUSINESS': 'Business Intelligence Dashboard',
      'WAREHOUSE_MANAGER': 'Warehouse Manager Dashboard',
      'STORE_MANAGER': 'Store Manager Dashboard',
      'LOGISTICS_MANAGER': 'Logistics Manager Dashboard',
      'ADMIN': 'Admin Dashboard'
    };
    return names[role] || 'Dashboard';
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} selectedRole={selectedRole} />
      <div style={{ marginLeft: '250px', padding: '30px', width: 'calc(100% - 250px)', boxSizing: 'border-box' }}>
        {/* Role Selector Button */}
        <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#64748b', fontSize: '14px' }}>Current Role:</span>
            <button
              onClick={handleRoleClick}
              style={{
                padding: '8px 16px',
                backgroundColor: getRoleColor(selectedRole),
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s ease',
                transform: roleChanged ? 'scale(1.05)' : 'scale(1)',
                boxShadow: roleChanged ? `0 0 20px ${getRoleColor(selectedRole)}50` : 'none'
              }}
            >
              {getRoleDisplayName(selectedRole)}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 9l6 6 6-6"/>
              </svg>
            </button>
          </div>

          {/* Visual indicator showing which dashboard is active */}
          <div style={{
            padding: '6px 12px',
            backgroundColor: `${getRoleColor(selectedRole)}15`,
            borderLeft: `3px solid ${getRoleColor(selectedRole)}`,
            borderRadius: '4px',
            fontSize: '12px',
            color: getRoleColor(selectedRole),
            fontWeight: '500'
          }}>
            Viewing: {getDashboardName(selectedRole)}
          </div>
        </div>

        {children}

        {/* Role Selector Modal */}
        {showRoleSelector && (
          <RoleSelector
            onRoleSelect={handleRoleSelect}
            onCancel={handleCancelRoleSelect}
            currentRole={selectedRole}
          />
        )}
      </div>
    </div>
  );
};

export default Layout;
