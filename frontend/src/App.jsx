import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import Forecast from './pages/Forecast';
import Alerts from './pages/Alerts';
import Orders from './pages/Orders';
import Deliveries from './pages/Deliveries';
import Warehouses from './pages/Warehouses';
import Stores from './pages/Stores';
import Logs from './pages/Logs';
import Intelligence from './pages/Intelligence';
import PredictiveIntelligence from './pages/PredictiveIntelligence';
import Orchestration from './pages/Orchestration';
import LLMOrchestration from './pages/LLMOrchestration';
import BusinessDashboard from './pages/dashboards/BusinessDashboard';
import WarehouseManagerDashboard from './pages/dashboards/WarehouseManagerDashboard';
import StoreManagerDashboard from './pages/dashboards/StoreManagerDashboard';
import LogisticsManagerDashboard from './pages/dashboards/LogisticsManagerDashboard';
import AdminDashboard from './pages/dashboards/AdminDashboard';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedRole, setSelectedRole] = useState('BUSINESS');

  const renderContent = () => {
    // For dashboard tab, show role-specific dashboard
    if (activeTab === 'dashboard') {
      switch (selectedRole) {
        case 'BUSINESS':
          return <BusinessDashboard userRole={selectedRole} />;
        case 'WAREHOUSE_MANAGER':
          return <WarehouseManagerDashboard userRole={selectedRole} />;
        case 'STORE_MANAGER':
          return <StoreManagerDashboard userRole={selectedRole} />;
        case 'LOGISTICS_MANAGER':
          return <LogisticsManagerDashboard userRole={selectedRole} />;
        case 'ADMIN':
          return <AdminDashboard userRole={selectedRole} />;
        default:
          return <BusinessDashboard userRole={selectedRole} />;
      }
    }

    // For other tabs, show generic pages
    switch (activeTab) {
      case 'intelligence':
        return <Intelligence />;
      case 'predictive':
        return <PredictiveIntelligence />;
      case 'orchestration':
        return <Orchestration />;
      case 'llm-orchestration':
        return <LLMOrchestration />;
      case 'inventory':
        return <Inventory />;
      case 'forecast':
        return <Forecast />;
      case 'alerts':
        return <Alerts />;
      case 'orders':
        return <Orders />;
      case 'deliveries':
        return <Deliveries />;
      case 'warehouses':
        return <Warehouses />;
      case 'stores':
        return <Stores />;
      case 'logs':
        return <Logs />;
      default:
        return <BusinessDashboard />;
    }
  };

  const handleRoleSelect = (role) => {
    console.log('Role selected in App:', role);
    setSelectedRole(role);
    // Reset to dashboard when switching roles
    setActiveTab('dashboard');
  };

  return (
    <Layout 
      activeTab={activeTab} 
      setActiveTab={setActiveTab}
      selectedRole={selectedRole}
      onRoleSelect={handleRoleSelect}
    >
      {renderContent()}
    </Layout>
  );
}

export default App;
