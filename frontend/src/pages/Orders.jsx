import React, { useEffect, useState } from 'react';
import { fetchOrders, triggerOrder } from '../services/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sku, setSku] = useState('');
  const [storeId, setStoreId] = useState('');
  const [quantity, setQuantity] = useState(10);
  const [orderLoad, setOrderLoad] = useState(false);

  const loadOrders = () => {
    fetchOrders()
      .then(res => {
        setOrders(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleCreateOrder = () => {
    if (!sku || !storeId) return alert('Please enter SKU and Store ID');
    setOrderLoad(true);
    triggerOrder(sku, storeId, quantity)
      .then(() => {
        alert('Order created successfully!');
        setSku('');
        setStoreId('');
        setQuantity(10);
        loadOrders();
      })
      .catch(err => {
        alert('Error creating order');
        console.error(err);
      })
      .finally(() => setOrderLoad(false));
  };

  // Prepare data for charts
  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'pending': return '#fef3c7';
      case 'delivered': return '#dcfce3';
      case 'shipped': return '#e0e7ff';
      default: return '#f1f5f9';
    }
  };

  const orderStatusData = [
    { name: 'Pending', value: orders.filter(o => o.status === 'pending').length, color: '#f59e0b' },
    { name: 'Delivered', value: orders.filter(o => o.status === 'delivered').length, color: '#22c55e' },
    { name: 'Shipped', value: orders.filter(o => o.status === 'shipped').length, color: '#3b82f6' },
    { name: 'Other', value: orders.filter(o => !['pending', 'delivered', 'shipped'].includes(o.status)).length, color: '#6b7280' }
  ].filter(d => d.value > 0);

  const orderAmountData = orders.slice(-10).map((order, index) => ({
    name: `Order ${index + 1}`,
    amount: order.total_amount || 0
  }));

  return (
    <div>
      <h1 style={{ color: '#0f172a', marginBottom: '20px' }}>Orders Management</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Order Status Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={orderStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {orderStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ marginTop: 0, color: '#334155', marginBottom: '15px' }}>Recent Order Amounts</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={orderAmountData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
              <Legend />
              <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} name="Amount" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '10px', marginBottom: '30px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
        <h3 style={{ marginTop: 0, color: '#334155' }}>Create New Order</h3>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Product SKU</label>
            <input type="text" value={sku} onChange={(e) => setSku(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1' }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Store ID</label>
            <input type="text" value={storeId} onChange={(e) => setStoreId(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1' }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Quantity</label>
            <input type="number" min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1' }} />
          </div>
          <button 
            onClick={handleCreateOrder} 
            disabled={orderLoad}
            style={{ 
              padding: '10px 20px', 
              backgroundColor: '#3b82f6', 
              color: 'white', 
              border: 'none', 
              borderRadius: '5px', 
              cursor: orderLoad ? 'not-allowed' : 'pointer',
              height: '40px',
              fontWeight: 'bold'
            }}
          >
            {orderLoad ? 'Creating...' : 'Trigger Order'}
          </button>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        <h3 style={{ margin: '20px', color: '#334155' }}>Order History</h3>
        {loading ? <div style={{ padding: '20px' }}>Loading orders...</div> : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '1px solid #e2e8f0' }}>
                <th style={{ padding: '15px' }}>Order ID</th>
                <th style={{ padding: '15px' }}>Store ID</th>
                <th style={{ padding: '15px' }}>Status</th>
                <th style={{ padding: '15px' }}>Total Amount</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.order_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '15px', fontWeight: 'bold' }}>{order.order_id}</td>
                  <td style={{ padding: '15px' }}>{order.store_id}</td>
                  <td style={{ padding: '15px' }}>
                    <span style={{ 
                      padding: '5px 10px', 
                      borderRadius: '20px', 
                      fontSize: '12px',
                      backgroundColor: order.status === 'pending' ? '#fef3c7' : order.status === 'delivered' ? '#dcfce3' : '#e0e7ff',
                      color: order.status === 'pending' ? '#d97706' : order.status === 'delivered' ? '#166534' : '#3730a3'
                    }}>
                      {order.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '15px' }}>${order.total_amount?.toFixed(2)}</td>
                </tr>
              ))}
              {orders.length === 0 && <tr><td colSpan="4" style={{ padding: '20px', textAlign: 'center' }}>No orders found</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Orders;
