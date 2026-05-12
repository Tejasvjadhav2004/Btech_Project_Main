import React, { useState, useEffect } from 'react';
import { 
  getInventoryWithStock,
  getActiveSignals,
  getWarehouses,
  getDashboardWarehouseStock,
  getDashboardLowStock
} from '../../services/api';
import { Package, BarChart3, AlertTriangle, CheckCircle2, TrendingUp, Factory, Siren, ClipboardList } from 'lucide-react';
import './WarehouseManagerDashboard.css';

function WarehouseManagerDashboard({ userRole }) {
  const [inventory, setInventory] = useState([]);
  const [signals, setSignals] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [warehouseStock, setWarehouseStock] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWarehouse, setSelectedWarehouse] = useState('all');

  useEffect(() => {
    loadWarehouseData();
  }, [selectedWarehouse, userRole]); // Add userRole to dependencies to re-fetch when role changes

  const loadWarehouseData = async () => {
    try {
      setLoading(true);
      const [inventoryData, signalsData, warehousesData, warehouseStockData, lowStockData] = await Promise.all([
        getInventoryWithStock(),
        getActiveSignals(),
        getWarehouses(),
        getDashboardWarehouseStock(),
        getDashboardLowStock()
      ]);

      setInventory(inventoryData || []);
      setSignals(signalsData.signals || []);
      setWarehouses(warehousesData.warehouses || []);
      setWarehouseStock(warehouseStockData?.warehouses || []);
      setLowStock(lowStockData || []);
    } catch (error) {
      console.error('Error loading warehouse dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWarehouseChange = (e) => {
    setSelectedWarehouse(e.target.value);
  };

  const filteredInventory = selectedWarehouse === 'all' 
    ? inventory 
    : inventory.filter(item => item.warehouse_id === selectedWarehouse);

  const lowStockSignals = signals.filter(s => s.type === 'LOW_STOCK');
  const overUtilizationSignals = signals.filter(s => s.type === 'OVER_UTILIZATION');

  if (loading) {
    return (
      <div className="warehouse-manager-dashboard">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading warehouse operations dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="warehouse-manager-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1><Package size={28} strokeWidth={1.8} style={{ verticalAlign: 'middle', marginRight: '10px' }} />Warehouse Manager Dashboard</h1>
          <p className="subtitle">Monitor inventory, allocations, and warehouse operations</p>
        </div>
        <div className="header-actions">
          <select 
            value={selectedWarehouse}
            onChange={handleWarehouseChange}
            className="warehouse-selector"
          >
            <option value="all">All Warehouses</option>
            {warehouses.map(warehouse => (
              <option key={warehouse.warehouse_id} value={warehouse.warehouse_id}>
                {warehouse.name} ({warehouse.warehouse_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card primary">
          <div className="kpi-icon"><BarChart3 size={24} /></div>
          <div className="kpi-content">
            <h3>Total Inventory</h3>
            <p className="kpi-value">{filteredInventory.length}</p>
            <p className="kpi-trend">SKUs tracked</p>
          </div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-icon"><AlertTriangle size={24} /></div>
          <div className="kpi-content">
            <h3>Low Stock Alerts</h3>
            <p className="kpi-value">{lowStock.length}</p>
            <p className="kpi-trend negative">Action needed</p>
          </div>
        </div>

        <div className="kpi-card success">
          <div className="kpi-icon"><CheckCircle2 size={24} /></div>
          <div className="kpi-content">
            <h3>Active Warehouses</h3>
            <p className="kpi-value">{warehouses.length}</p>
            <p className="kpi-trend">All operational</p>
          </div>
        </div>

        <div className="kpi-card info">
          <div className="kpi-icon"><TrendingUp size={24} /></div>
          <div className="kpi-content">
            <h3>Avg Stock Level</h3>
            <p className="kpi-value">
              {filteredInventory.length > 0 
                ? Math.round(filteredInventory.reduce((sum, item) => sum + (item.current_stock || item.quantity || 0), 0) / filteredInventory.length)
                : 0}
            </p>
            <p className="kpi-trend">units per SKU</p>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Low Stock Items */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h3><AlertTriangle size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Low Stock Items</h3>
            <span className="badge warning">{lowStock.length} items</span>
          </div>
          <div className="card-content">
            {lowStock.length > 0 ? (
              <div className="low-stock-table">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>SKU</th>
                      <th>Warehouse</th>
                      <th>Current Stock</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lowStock.slice(0, 10).map((item, index) => (
                      <tr key={index}>
                        <td>
                          <div className="product-info">
                            <span className="product-name">{item.product_name || item.sku}</span>
                          </div>
                        </td>
                        <td>{item.sku}</td>
                         <td>{item.warehouse_id}</td>
                         <td>
                           <span className="stock-value critical">{item.current_stock || item.quantity || 0}</span>
                         </td>
                         <td>
                           <span className="status-badge critical">Critical</span>
                         </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p><CheckCircle2 size={16} style={{ verticalAlign: 'middle', marginRight: '6px', color: '#22c55e' }} />No low stock items detected</p>
              </div>
            )}
          </div>
        </div>

        {/* Warehouse Stock Overview */}
        <div className="dashboard-card">
          <div className="card-header">
            <h3><Factory size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Warehouse Stock Overview</h3>
          </div>
          <div className="card-content">
            <div className="warehouse-stock-list">
              {warehouseStock.slice(0, 6).map((warehouse, index) => (
                <div key={index} className="warehouse-stock-item">
                  <div className="warehouse-info">
                    <h4>{warehouse.warehouse_id}</h4>
                    <p>{warehouse.total_stock || 0} total units</p>
                  </div>
                  <div className="stock-breakdown">
                    <div className="stock-metric">
                      <span className="label">Allocated:</span>
                      <span className="value">{warehouse.allocated_stock || 0}</span>
                    </div>
                    <div className="stock-metric">
                      <span className="label">Available:</span>
                      <span className="value">{warehouse.available_stock || 0}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Active Signals */}
        <div className="dashboard-card">
          <div className="card-header">
            <h3><Siren size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Active Signals</h3>
            <span className="badge">{signals.length}</span>
          </div>
          <div className="card-content">
            {signals.length > 0 ? (
              <div className="signals-list">
                {signals.slice(0, 8).map((signal) => (
                  <div key={signal.signal_id} className="signal-item">
                    <div className="signal-header">
                      <span className={`signal-type ${signal.type.toLowerCase()}`}>
                        {signal.type.replace('_', ' ')}
                      </span>
                      <span className={`signal-severity ${signal.severity.toLowerCase()}`}>
                        {signal.severity}
                      </span>
                    </div>
                    <p className="signal-message">{signal.message}</p>
                    <div className="signal-footer">
                      <span className="signal-entity">{signal.entity_id}</span>
                      <span className="signal-time">
                        {new Date(signal.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p><CheckCircle2 size={16} style={{ verticalAlign: 'middle', marginRight: '6px', color: '#22c55e' }} />No active signals</p>
              </div>
            )}
          </div>
        </div>

        {/* Inventory Breakdown */}
        <div className="dashboard-card full-width">
          <div className="card-header">
            <h3><ClipboardList size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Inventory Breakdown</h3>
            <span className="badge">{filteredInventory.length} items</span>
          </div>
          <div className="card-content">
            <div className="inventory-table">
              <table>
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Product</th>
                    <th>Warehouse</th>
                    <th>Available</th>
                    <th>Allocated</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                   {filteredInventory.slice(0, 15).map((item, index) => (
                     <tr key={index}>
                       <td className="sku-cell">{item.sku}</td>
                       <td>{item.product_name || item.sku}</td>
                       <td>{item.warehouse_id}</td>
                       <td>{item.current_stock || item.quantity || 0}</td>
                       <td>{item.allocated_quantity || 0}</td>
                       <td>
                         {(item.current_stock || item.quantity) < 10 ? (
                           <span className="status-badge critical">Low</span>
                         ) : (item.current_stock || item.quantity) < 50 ? (
                           <span className="status-badge warning">Medium</span>
                         ) : (
                           <span className="status-badge success">Good</span>
                         )}
                       </td>
                     </tr>
                   ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WarehouseManagerDashboard;
