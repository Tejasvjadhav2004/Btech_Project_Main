import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
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
import DemoControl from './pages/DemoControl';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedRole, setSelectedRole] = useState('ADMIN');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard userRole={selectedRole} />;
      case 'demo':
        return <DemoControl />;
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
        return <Dashboard userRole={selectedRole} />;
    }
  };

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
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
