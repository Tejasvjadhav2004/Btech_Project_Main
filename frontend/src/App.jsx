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

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'intelligence':
        return <Intelligence />;
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
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </Layout>
  );
}

export default App;
