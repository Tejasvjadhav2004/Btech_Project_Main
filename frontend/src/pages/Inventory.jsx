import React, { useEffect, useState } from 'react';
import { getInventoryWithStock, getProductsList } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const Inventory = () => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const inventoryRes = await getInventoryWithStock();
        
        // Fetch products to get metadata (names, descriptions)
        const productsRes = await getProductsList();
        
        // Create a product lookup map
        const productMap = new Map(productsRes.map(p => [p.sku, p]));
        
        // Enhance inventory data with product metadata
        const enhancedInventory = inventoryRes.map(inv => {
          const product = productMap.get(inv.sku);
          return {
            ...inv,
            productName: product?.name || inv.sku,
            productCategory: product?.category || 'Unknown',
            productPrice: product?.current_price || 0
          };
        });
        
        setInventory(enhancedInventory);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching inventory data:', err);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Reset to page 1 when search term changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  if (loading) return <div>Loading inventory...</div>;

  const filteredInventory = inventory.filter(inv => 
    inv.productName.toLowerCase().includes(searchTerm.toLowerCase()) || 
    inv.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (inv.location_id && inv.location_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Pagination logic
  const totalItems = filteredInventory.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedInventory = filteredInventory.slice(startIndex, endIndex);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(totalPages, prev + 1));
  };

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

  const getInventoryStatusColor = (status) => {
    switch (status) {
      case 'Low Stock': return '#ef4444';
      case 'Overstocked': return '#f97316';
      case 'Healthy': return '#22c55e';
      default: return '#64748b';
    }
  };

  // Prepare data for charts
  const stockStatusData = [
    { name: 'Low Stock', value: inventory.filter(inv => inv.current_stock < 20).length, color: '#ef4444' },
    { name: 'Normal Stock', value: inventory.filter(inv => inv.current_stock >= 20 && inv.current_stock <= 150).length, color: '#22c55e' },
    { name: 'Overstock', value: inventory.filter(inv => inv.current_stock > 150).length, color: '#f97316' }
  ];

  const warehouseStockData = inventory.reduce((acc, item) => {
    if (item.location_type === 'warehouse') {
      const existing = acc.find(d => d.name === item.location_id);
      if (existing) {
        existing.stock += item.current_stock || 0;
      } else {
        acc.push({ name: item.location_id, stock: item.current_stock || 0 });
      }
    }
    return acc;
  }, []);

  const topStockedProducts = [...inventory]
    .sort((a, b) => b.current_stock - a.current_stock)
    .slice(0, 10)
    .map(inv => ({ name: inv.productName.substring(0, 20), stock: inv.current_stock }));

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
        placeholder="Search by product name, SKU, or location..." 
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
              <th style={{ padding: '15px', color: '#475569' }}>Location</th>
              <th style={{ padding: '15px', color: '#475569' }}>Location Type</th>
              <th style={{ padding: '15px', color: '#475569' }}>Current Stock</th>
              <th style={{ padding: '15px', color: '#475569' }}>Available Stock</th>
              {/* <th style={{ padding: '15px', color: '#475569' }}>Reserved Stock</th> */}
              {/* <th style={{ padding: '15px', color: '#475569' }}>Incoming Stock</th> */}
              {/* <th style={{ padding: '15px', color: '#475569' }}>Damaged Stock</th> */}
              <th style={{ padding: '15px', color: '#475569' }}>Status</th>
              <th style={{ padding: '15px', color: '#475569' }}>Transactions</th>
              <th style={{ padding: '15px', color: '#475569' }}>Total Sales</th>
            </tr>
          </thead>
          <tbody>
            {paginatedInventory.map(inv => (
              
              <tr key={`${inv.sku}-${inv.location_id}`} style={{ ...getRowStyle(inv.current_stock), borderBottom: '1px solid #e2e8f0' }}>
                 {console.log('Rendering inventory item:', inv)}
                <td style={{ padding: '15px', color: '#0f172a', fontWeight: '500' }}>{inv.productName}</td>
                <td style={{ padding: '15px', color: '#64748b' }}>{inv.sku}</td>
                <td style={{ padding: '15px', color: '#0f172a' }}>{inv.location_id}</td>
                <td style={{ padding: '15px', color: '#64748b' }}>{inv.location_type}</td>
                <td style={{ padding: '15px', color: '#0f172a' }}>
                  <span style={getBadgeStyle(inv.current_stock)}>
                    {inv.current_stock} units
                  </span>
                </td>
                <td style={{ padding: '15px', color: '#0f172a' }}>
                  <span style={{ backgroundColor: '#10b981', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '12px' }}>
                    {inv.available_stock} units
                  </span>
                </td>
                {/* <td style={{ padding: '15px', color: '#64748b' }}>{inv.reserved_stock} units</td> */}
                {/* <td style={{ padding: '15px', color: '#64748b' }}>{inv.incoming_stock || 0} units</td> */}
                {/* <td style={{ padding: '15px', color: '#64748b' }}>{inv.damaged_stock || 0} units</td> */}
                <td style={{ padding: '15px', color: '#0f172a' }}>
                  <span style={{
                    backgroundColor: getInventoryStatusColor(inv.inventory_status || 'Healthy'),
                    color: 'white',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '12px'
                  }}>
                    {inv.inventory_status || 'Healthy'}
                  </span>
                </td>
                <td style={{ padding: '15px', color: '#64748b' }}>{inv.transactions_count}</td>
                <td style={{ padding: '15px', color: '#64748b' }}>{inv.total_sales} units</td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div style={{ 
            padding: '15px', 
            borderTop: '1px solid #e2e8f0', 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            backgroundColor: '#f8fafc'
          }}>
            <div style={{ color: '#64748b', fontSize: '14px' }}>
              Showing {startIndex + 1} to {Math.min(endIndex, totalItems)} of {totalItems} records
              {searchTerm && ` (filtered from ${inventory.length} total)`}
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                style={{
                  padding: '6px 12px',
                  backgroundColor: currentPage === 1 ? '#e2e8f0' : '#3b82f6',
                  color: currentPage === 1 ? '#94a3b8' : 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                  fontSize: '14px'
                }}
              >
                Previous
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: currentPage === pageNum ? '#3b82f6' : 'white',
                      color: currentPage === pageNum ? 'white' : '#0f172a',
                      border: currentPage === pageNum ? 'none' : '1px solid #e2e8f0',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {pageNum}
                  </button>
                );
              })}
              
              <button 
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                style={{
                  padding: '6px 12px',
                  backgroundColor: currentPage === totalPages ? '#e2e8f0' : '#3b82f6',
                  color: currentPage === totalPages ? '#94a3b8' : 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                  fontSize: '14px'
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}
        
        {filteredInventory.length === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>No inventory records found</div>
        )}
      </div>
    </div>
  );
};

export default Inventory;
