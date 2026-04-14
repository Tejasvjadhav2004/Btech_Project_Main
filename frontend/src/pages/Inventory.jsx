import React, { useEffect, useState } from 'react';
import { getProductsList, getInventoryWithStock } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const Inventory = () => {
  const [products, setProducts] = useState([]);
  const [inventoryData, setInventoryData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, inventoryRes] = await Promise.all([
          getProductsList(),
          getInventoryWithStock()
        ]);
        
        // Merge product data with inventory data to get real stock levels
        const enhancedProducts = productsRes.map(product => {
          const inventoryRecord = inventoryRes.find(inv => inv.sku === product.sku);
          return {
            ...product,
            stockLevel: inventoryRecord?.stock || 0,
            warehouse: inventoryRecord?.location_id || (product.warehouse || 'Unknown'),
            locationType: inventoryRecord?.location_type || 'warehouse'
          };
        });
        
        setProducts(enhancedProducts);
        setInventoryData(inventoryRes);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching inventory data:', err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading inventory...</div>;

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.warehouse && p.warehouse.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getRowStyle = (stockLevel) => {
    if (stockLevel < 20) return { backgroundColor: '#fee2e2' }; // Low stock (red)
    if (stockLevel > 150) return { backgroundColor: '#ffedd5' }; // Overstock (orange)
    return { backgroundColor: 'white' };
  };

  const getBadgeStyle = (stockLevel) => {
    if (stockLevel < 20) return { backgroundColor: '#ef4444', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '12px' };
    if (stockLevel > 150) return { backgroundColor: '#f97316', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '12px' };
    return { backgroundColor: '#22c55e', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '12px' };
  };

  // Prepare data for charts
  const stockStatusData = [
    { name: 'Low Stock', value: products.filter(p => p.stockLevel < 20).length, color: '#ef4444' },
    { name: 'Normal Stock', value: products.filter(p => p.stockLevel >= 20 && p.stockLevel <= 150).length, color: '#22c55e' },
    { name: 'Overstock', value: products.filter(p => p.stockLevel > 150).length, color: '#f97316' }
  ];

  const warehouseStockData = inventoryData.reduce((acc, item) => {
    if (item.location_type === 'warehouse') {
      const existing = acc.find(d => d.name === item.location_id);
      if (existing) {
        existing.stock += item.stock || 0;
      } else {
        acc.push({ name: item.location_id, stock: item.stock || 0 });
      }
    }
    return acc;
  }, []);

  const topStockedProducts = [...products]
    .sort((a, b) => b.stockLevel - a.stockLevel)
    .slice(0, 10)
    .map(p => ({ name: p.name.substring(0, 20), stock: p.stockLevel }));

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Inventory Management</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Stock Status Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={stockStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {stockStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Stock by Warehouse</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={warehouseStockData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="stock" fill="#3b82f6" name="Stock Units" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '30px' }}>
        <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Top 10 Products by Stock Level</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={topStockedProducts}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="stock" stroke="#10b981" fill="#10b981" fillOpacity={0.6} name="Stock Units" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      <input 
        type="text" 
        placeholder="Search by name, SKU, or warehouse..." 
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        style={{
          padding: '10px 15px',
          width: '350px',
          borderRadius: '5px',
          border: '1px solid #cbd5e1',
          marginBottom: '20px',
          fontSize: '14px'
        }}
      />

      <div style={{ overflowX: 'auto', backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
              <th style={{ padding: '15px', color: '#475569' }}>Product Name</th>
              <th style={{ padding: '15px', color: '#475569' }}>SKU</th>
              <th style={{ padding: '15px', color: '#475569' }}>Warehouse/Store</th>
              <th style={{ padding: '15px', color: '#475569' }}>Stock Level</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map(product => (
              <tr key={product.sku} style={{ ...getRowStyle(product.stockLevel), borderBottom: '1px solid #e2e8f0' }}>
                <td style={{ padding: '15px', color: '#0f172a', fontWeight: '500' }}>{product.name}</td>
                <td style={{ padding: '15px', color: '#64748b' }}>{product.sku}</td>
                <td style={{ padding: '15px', color: '#0f172a' }}>
                  {product.warehouse || 'Unknown'} ({product.locationType || 'warehouse'})
                </td>
                <td style={{ padding: '15px', color: '#0f172a' }}>
                  <span style={getBadgeStyle(product.stockLevel)}>
                    {product.stockLevel} units
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredProducts.length === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No products found</div>
        )}
      </div>
    </div>
  );
};

export default Inventory;
