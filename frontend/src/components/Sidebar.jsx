import React from 'react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'intelligence', label: 'Intelligence' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'forecast', label: 'Demand Forecast' },
    { id: 'alerts', label: 'Alerts' },
    { id: 'orders', label: 'Orders' },
    { id: 'deliveries', label: 'Deliveries' },
    { id: 'warehouses', label: 'Warehouses' },
    { id: 'stores', label: 'Stores' },
    { id: 'logs', label: 'Logs / Anomalies' }
  ];

  return (
    <div style={{
      width: '250px',
      height: '100vh',
      backgroundColor: '#1e293b',
      color: 'white',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 0',
      position: 'fixed',
      left: 0,
      top: 0
    }}>
      <h2 style={{ padding: '0 20px', marginBottom: '30px', color: '#38bdf8' }}>SCM System</h2>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '15px 20px',
              textAlign: 'left',
              backgroundColor: activeTab === tab.id ? '#334155' : 'transparent',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: '16px',
              transition: 'background-color 0.2s',
              borderLeft: activeTab === tab.id ? '4px solid #38bdf8' : '4px solid transparent'
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;
