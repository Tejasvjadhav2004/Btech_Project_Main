import React, { useEffect, useState } from 'react';
import { getProductsList } from '../services/api';

const Inventory = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    getProductsList()
      .then(res => {
        // Simulating stock level and warehouse until API fully supports it
        const enhancedProducts = res.map((p, index) => ({
          ...p,
          stockLevel: Math.floor(Math.random() * 200),
          warehouse: `WH-${(index % 3) + 1}`,
        }));
        setProducts(enhancedProducts);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading inventory...</div>;

  const filteredProducts = products.filter(p => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.warehouse.toLowerCase().includes(searchTerm.toLowerCase())
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

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Inventory Management</h1>
      
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
                <td style={{ padding: '15px', color: '#0f172a' }}>{product.warehouse}</td>
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
