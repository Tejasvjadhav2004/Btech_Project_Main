import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setCurrentRole, getAvailableRoles } from '../services/api';
import { BarChart3, Package, Store, Truck, Settings, User, Check } from 'lucide-react';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState('');
  const [loading, setLoading] = useState(false);

  const roles = getAvailableRoles();

  const handleRoleSelect = (roleId) => {
    setSelectedRole(roleId);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    console.log('=== LOGIN FLOW DEBUG ===');
    console.log('1. handleLogin called');
    console.log('2. selectedRole:', selectedRole);
    
    if (!selectedRole) {
      alert('Please select a role');
      return;
    }

    setLoading(true);
    console.log('3. Setting loading to true');
    
    // Simulate a brief delay for better UX
    setTimeout(() => {
      console.log('4. Inside setTimeout - about to call setCurrentRole');
      setCurrentRole(selectedRole);
      console.log('5. setCurrentRole called with:', selectedRole);
      setLoading(false);
      // Note: We don't need navigate() anymore since App.jsx listens for role changes
      console.log('6. Login complete - state change will trigger navigation');
    }, 500);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Supply Chain Management System</h1>
          <h2>Select Your Role</h2>
          <p className="login-subtitle">Choose your stakeholder role to access the dashboard</p>
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          <div className="roles-grid">
            {roles.map((role) => (
              <div
                key={role.id}
                className={`role-card ${selectedRole === role.id ? 'selected' : ''}`}
                onClick={() => handleRoleSelect(role.id)}
              >
                <div className="role-icon">
                  {getRoleIcon(role.id)}
                </div>
                <h3>{role.name}</h3>
                <p>{role.description}</p>
                {selectedRole === role.id && (
                  <div className="role-selected-badge">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Selected</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          <button 
            type="submit" 
            className="login-button" 
            disabled={!selectedRole || loading}
          >
            {loading ? 'Loading...' : 'Access Dashboard'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            <strong>Note:</strong> This is a simplified authentication system for demonstration purposes. 
            No password is required - simply select your role to access the system.
          </p>
        </div>
      </div>
    </div>
  );
}

function getRoleIcon(roleId) {
  const iconProps = { size: 32, strokeWidth: 1.6, color: '#3b82f6' };
  const icons = {
    'BUSINESS': <BarChart3 {...iconProps} />,
    'WAREHOUSE_MANAGER': <Package {...iconProps} />,
    'STORE_MANAGER': <Store {...iconProps} />,
    'LOGISTICS_MANAGER': <Truck {...iconProps} />,
    'ADMIN': <Settings {...iconProps} />,
  };
  return icons[roleId] || <User {...iconProps} />;
}

export default Login;
