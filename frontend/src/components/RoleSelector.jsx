import React, { useState } from 'react';
import { getAvailableRoles } from '../services/api';
import { BarChart3, Package, Store, Truck, Settings, User, Check } from 'lucide-react';

const RoleSelector = ({ onRoleSelect, onCancel, currentRole }) => {
  console.log('RoleSelector component mounted, currentRole:', currentRole);
  const [selectedRole, setSelectedRole] = useState(currentRole || '');
  const roles = getAvailableRoles();

  const handleRoleSelect = (roleId) => {
    console.log('Role selected in modal:', roleId);
    setSelectedRole(roleId);
    console.log('Selected role updated to:', roleId);
  };

  const handleConfirm = () => {
    console.log('Confirming role selection:', selectedRole);
    if (selectedRole) {
      onRoleSelect(selectedRole);
    }
  };

  const getRoleColor = (roleId) => {
    const colors = {
      'BUSINESS': '#3b82f6',
      'WAREHOUSE_MANAGER': '#f59e0b',
      'STORE_MANAGER': '#10b981',
      'LOGISTICS_MANAGER': '#8b5cf6',
      'ADMIN': '#ef4444'
    };
    return colors[roleId] || '#3b82f6';
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '10px',
        width: '450px',
        maxWidth: '90vw',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}>
        <h2 style={{ marginTop: 0, color: '#333', textAlign: 'center' }}>Switch Role</h2>
        <p style={{ textAlign: 'center', color: '#666', marginBottom: '20px' }}>
          Select a role to see its specialized dashboard
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '20px' }}>
          {roles.map((role) => (
            <div
              key={role.id}
              style={{
                padding: '15px',
                border: `2px solid ${selectedRole === role.id ? getRoleColor(role.id) : '#e5e7eb'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: selectedRole === role.id ? `${getRoleColor(role.id)}10` : 'white',
                transition: 'all 0.2s',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                position: 'relative'
              }}
              onClick={() => handleRoleSelect(role.id)}
            >
              {selectedRole === role.id && (
                <div style={{
                  position: 'absolute',
                  top: '8px',
                  right: '8px',
                  backgroundColor: getRoleColor(role.id),
                  borderRadius: '50%',
                  width: '20px',
                  height: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Check size={14} color="white" strokeWidth={3} />
                </div>
              )}
              <div style={{ fontSize: '24px', marginBottom: '8px', color: getRoleColor(role.id) }}>
                {getRoleIcon(role.id)}
              </div>
              <h4 style={{ margin: '0 0 5px 0', fontSize: '14px', color: selectedRole === role.id ? getRoleColor(role.id) : '#333' }}>
                {role.name}
              </h4>
              <p style={{ margin: 0, fontSize: '11px', color: '#666', textAlign: 'center' }}>{role.description}</p>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
          <button
            onClick={onCancel}
            style={{
              padding: '10px 20px',
              backgroundColor: '#f3f4f6',
              color: '#374151',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selectedRole || selectedRole === currentRole}
            style={{
              padding: '10px 20px',
              backgroundColor: selectedRole && selectedRole !== currentRole ? '#3b82f6' : '#e5e7eb',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: selectedRole && selectedRole !== currentRole ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            {selectedRole === currentRole ? 'Already Selected' : 'Switch Role'}
          </button>
        </div>
      </div>
    </div>
  );
};

function getRoleIcon(roleId) {
  const iconProps = { size: 28, strokeWidth: 1.6, color: '#3b82f6' };
  const icons = {
    'BUSINESS': <BarChart3 {...iconProps} />,
    'WAREHOUSE_MANAGER': <Package {...iconProps} />,
    'STORE_MANAGER': <Store {...iconProps} />,
    'LOGISTICS_MANAGER': <Truck {...iconProps} />,
    'ADMIN': <Settings {...iconProps} />,
  };
  return icons[roleId] || <User {...iconProps} />;
}

export default RoleSelector;