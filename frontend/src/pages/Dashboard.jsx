import React, { useEffect, useState } from 'react';
import { getDashboardOverview, getDashboardProductStock, getDashboardWarehouseStock, getDashboardStoreStock, getDashboardLowStock, getDashboardMetrics } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [overview, setOverview] = useState(null);
  const [productStock, setProductStock] = useState([]);
  const [warehouseStock, setWarehouseStock] = useState([]);
  const [storeStock, setStoreStock] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAllData = async () => {
      try {
        const [overviewData, productStockData, warehouseStockData, storeStockData, lowStockData, metricsData] = await Promise.all([
          getDashboardOverview(),
          getDashboardProductStock(),
          getDashboardWarehouseStock(),
          getDashboardStoreStock(),
          getDashboardLowStock(),
          getDashboardMetrics()
        ]);
        setOverview(overviewData);
        setProductStock(Array.isArray(productStockData?.distribution) ? productStockData.distribution : []);
        setWarehouseStock(Array.isArray(warehouseStockData?.warehouses) ? warehouseStockData.warehouses : []);
        setStoreStock(Array.isArray(storeStockData?.stores) ? storeStockData.stores : []);
        setLowStock(Array.isArray(lowStockData?.items) ? lowStockData.items : []);
        setMetrics(metricsData || {});
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAllData();
  }, []);

  if (loading) return <div>Loading dashboard...</div>;
  if (!overview) return <div>Error loading dashboard data.</div>;

  // Prepare data for charts using real API data
  // Stock distribution by category - using product stock data
  const categoryData = productStock.reduce((acc, item) => {
    const existing = acc.find(d => d.name === (item.category || 'Other'));
    if (existing) {
      existing.value += item.total_quantity || item.quantity || 0;
    } else {
      acc.push({ name: item.category || 'Other', value: item.total_quantity || item.quantity || 0, color: getColorForCategory(item.category) });
    }
    return acc;
  }, []).slice(0, 6);

  // Top 10 products by revenue - using product stock data (assuming stock correlates with demand)
  const topProductsData = productStock
    .sort((a, b) => (b.total_revenue || b.total_sales || 0) - (a.total_revenue || a.total_sales || 0))
    .slice(0, 10)
    .map(item => ({
      name: (item.name || item.product_name || item.sku || 'Unknown').substring(0, 20),
      revenue: item.total_revenue || item.total_sales || 0
    }));

  // Warehouse utilization and stock
  const warehouseData = warehouseStock.map(wh => ({
    name: wh.warehouse_id || wh.name || 'Unknown',
    utilization: wh.utilization_rate || wh.utilization || 0,
    stock: wh.current_utilization || 0
  }));

  function getColorForCategory(category) {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
    const index = Math.abs((category || '').length) % colors.length;
    return colors[index];
  }

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Dashboard Overview</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
        <Card title="Total Products" value={overview.total_products || 0} />
        <Card title="Total Stock" value={overview.total_stock || 0} />
        <Card title="Low Stock Alerts" value={overview.low_stock_alerts || 0} color={(overview.low_stock_alerts || 0) > 0 ? '#ef4444' : '#22c55e'} />
        <Card title="Warehouse Utilization" value={`${(overview.warehouse_utilization || 0).toFixed(1)}%`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155' }}>Stock Distribution by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155' }}>Top 10 Products by Revenue</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topProductsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="revenue" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '30px' }}>
        <h3 style={{ marginTop: 0, color: '#334155' }}>Warehouse Utilization & Stock Levels</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={warehouseData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="utilization" fill="#10b981" name="Utilization %" />
            <Bar yAxisId="right" dataKey="stock" fill="#3b82f6" name="Stock Units" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h3 style={{ marginTop: 0, color: '#334155' }}>Recent Activity</h3>
        <p style={{ color: '#64748b', fontSize: '18px' }}>Total Revenue: <strong style={{ color: '#0f172a' }}>${overview.total_revenue?.toLocaleString() || '0'}</strong></p>
      </div>
    </div>
  );
};

const Card = ({ title, value, color }) => (
  <div style={{
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '10px',
    boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
    borderLeft: color ? `4px solid ${color}` : '4px solid #38bdf8'
  }}>
    <h3 style={{ margin: 0, fontSize: '14px', color: '#64748b', fontWeight: 'normal' }}>{title}</h3>
    <p style={{ margin: '10px 0 0 0', fontSize: '24px', fontWeight: 'bold', color: color || '#0f172a' }}>{value}</p>
  </div>
);

export default Dashboard;
