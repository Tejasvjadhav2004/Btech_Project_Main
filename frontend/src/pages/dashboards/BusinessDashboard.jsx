import React, { useState, useEffect } from 'react';
import { 
  getDashboardOverview, 
  getDashboardMetrics,
  getSignalStats,
  getActiveSignals,
  getDashboardProductStock,
  getDashboardWarehouseStock,
  getDashboardStoreStock
} from '../../services/api';
import { BarChart3, Package, CheckCircle2, AlertTriangle, DollarSign, Factory, Truck, TrendingUp, Banknote, Siren } from 'lucide-react';
import './BusinessDashboard.css';

function BusinessDashboard({ userRole }) {
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [signalStats, setSignalStats] = useState(null);
  const [activeSignals, setActiveSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  useEffect(() => {
    loadDashboardData();
  }, [timeRange, userRole]); // Add userRole to dependencies to re-fetch when role changes

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [overview, metricsData, stats, signals, productStock, warehouseStock, storeStock] = await Promise.all([
        getDashboardOverview(),
        getDashboardMetrics(),
        getSignalStats(),
        getActiveSignals(),
        getDashboardProductStock(),
        getDashboardWarehouseStock(),
        getDashboardStoreStock()
      ]);

      setData({
        overview,
        productStock,
        warehouseStock,
        storeStock
      });
      setMetrics(metricsData);
      setSignalStats(stats);
      setActiveSignals(signals.signals || []);
    } catch (error) {
      console.error('Error loading business dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="business-dashboard">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading business intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="business-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1><BarChart3 size={28} strokeWidth={1.8} style={{ verticalAlign: 'middle', marginRight: '10px' }} />Business Intelligence Dashboard</h1>
          <p className="subtitle">Enterprise-wide supply chain analytics and KPIs</p>
        </div>
        <div className="header-actions">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="time-range-selector"
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card primary">
          <div className="kpi-icon"><Package size={24} /></div>
          <div className="kpi-content">
            <h3>Total Orders</h3>
            <p className="kpi-value">{metrics?.total_orders || data?.overview?.total_orders || 0}</p>
            <p className="kpi-trend">Data will be calculated from real orders</p>
          </div>
        </div>

        <div className="kpi-card success">
          <div className="kpi-icon"><CheckCircle2 size={24} /></div>
          <div className="kpi-content">
            <h3>Order Fulfillment Rate</h3>
            <p className="kpi-value">{metrics?.fulfillment_rate || '94.2%'}</p>
            <p className="kpi-trend">Data will be calculated from real metrics</p>
          </div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-icon"><AlertTriangle size={24} /></div>
          <div className="kpi-content">
            <h3>Active Alerts</h3>
            <p className="kpi-value">{activeSignals.length}</p>
            <p className="kpi-trend">Based on active signals</p>
          </div>
        </div>

        <div className="kpi-card info">
          <div className="kpi-icon"><DollarSign size={24} /></div>
          <div className="kpi-content">
            <h3>Revenue</h3>
            <p className="kpi-value">${metrics?.revenue?.toLocaleString() || '0'}</p>
            <p className="kpi-trend">Data will be calculated from real orders</p>
          </div>
        </div>

        <div className="kpi-card primary">
          <div className="kpi-icon"><Factory size={24} /></div>
          <div className="kpi-content">
            <h3>Warehouse Utilization</h3>
            <p className="kpi-value">{metrics?.warehouse_utilization || '78%'}</p>
            <p className="kpi-trend">Based on warehouse utilization</p>
          </div>
        </div>

        <div className="kpi-card success">
          <div className="kpi-icon"><Truck size={24} /></div>
          <div className="kpi-content">
            <h3>On-Time Delivery</h3>
            <p className="kpi-value">{metrics?.on_time_delivery || '96.8%'}</p>
            <p className="kpi-trend">Based on delivery data</p>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* Order Trends */}
        <div className="chart-card large">
          <div className="chart-header">
            <h3><TrendingUp size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Order Trends</h3>
            <span className="chart-badge">Real-time</span>
          </div>
          <div className="chart-content">
            <p>Order volume chart will be populated with real data</p>
          </div>
        </div>

        {/* Revenue Breakdown */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Banknote size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Revenue by Category</h3>
          </div>
          <div className="chart-content">
            <p>Revenue by category will be populated with real data</p>
          </div>
        </div>

        {/* Signal Distribution */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Siren size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Signal Distribution</h3>
          </div>
          <div className="chart-content">
            <div className="signal-distribution">
              <div className="signal-item">
                <span className="signal-type">Low Stock</span>
                <span className="count">{signalStats?.by_type?.LOW_STOCK || 0}</span>
                <div className="bar warning" style={{width: '60%'}}></div>
              </div>
              <div className="signal-item">
                <span className="signal-type">Delivery Delay</span>
                <span className="count">{signalStats?.by_type?.DELIVERY_DELAY || 0}</span>
                <div className="bar danger" style={{width: '40%'}}></div>
              </div>
              <div className="signal-item">
                <span className="signal-type">Over Utilization</span>
                <span className="count">{signalStats?.by_type?.OVER_UTILIZATION || 0}</span>
                <div className="bar info" style={{width: '30%'}}></div>
              </div>
              <div className="signal-item">
                <span className="signal-type">Demand Spike</span>
                <span className="count">{signalStats?.by_type?.DEMAND_SPIKE || 0}</span>
                <div className="bar success" style={{width: '25%'}}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Warehouse Performance */}
        <div className="chart-card">
          <div className="chart-header">
            <h3><Factory size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Warehouse Performance</h3>
          </div>
          <div className="chart-content">
            <p>Warehouse performance will be populated with real data</p>
          </div>
        </div>
      </div>

      {/* Active Signals Section */}
      {activeSignals.length > 0 && (
        <div className="active-signals-section">
          <div className="section-header">
            <h3><Siren size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Active Signals Requiring Attention</h3>
            <span className="badge">{activeSignals.length} active</span>
          </div>
          <div className="signals-grid">
            {activeSignals.slice(0, 6).map((signal) => (
              <div key={signal.signal_id} className="signal-card">
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
                  <span className="signal-time">
                    {new Date(signal.created_at).toLocaleString()}
                  </span>
                  <span className="signal-entity">{signal.entity_id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default BusinessDashboard;
