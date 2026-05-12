import React, { useState, useEffect } from 'react';
import { 
  fetchOrders,
  getStores,
  triggerOrder,
  getProductsList
} from '../../services/api';
import { Store, ClipboardList, Hourglass, Truck, CheckCircle2, Package } from 'lucide-react';
import './StoreManagerDashboard.css';

function StoreManagerDashboard({ userRole }) {
  const [orders, setOrders] = useState([]);
  const [stores, setStores] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [newOrder, setNewOrder] = useState({
    sku: '',
    store_id: '',
    quantity: 10
  });

  useEffect(() => {
    loadStoreData();
  }, [userRole]); // Add userRole to dependencies to re-fetch when role changes

  const loadStoreData = async () => {
    try {
      console.log('=== StoreManagerDashboard loadStoreData ===');
      console.log('1. Starting to fetch data...');
      setLoading(true);
      const [ordersData, storesData, productsData] = await Promise.all([
        fetchOrders(),
        getStores(),
        getProductsList()
      ]);

      console.log('2. Data received from API calls:');
      console.log('   - ordersData:', ordersData);
      console.log('   - storesData:', storesData);
      console.log('   - productsData:', productsData);

      console.log('3. Processing data for state:');
      console.log('   - Setting orders:', ordersData.orders || ordersData || []);
      console.log('   - Setting stores:', storesData.stores || storesData || []);
      console.log('   - Setting products:', productsData.products || productsData || []);

      setOrders(ordersData.orders || ordersData || []);
      setStores(storesData.stores || storesData || []);
      setProducts(productsData.products || productsData || []);

      console.log('4. State updated successfully');
    } catch (error) {
      console.error('Error loading store dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    try {
      await triggerOrder(newOrder.sku, newOrder.store_id, newOrder.quantity);
      setShowCreateOrder(false);
      setNewOrder({ sku: '', store_id: '', quantity: 10 });
      loadStoreData();
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Failed to create order');
    }
  };

  if (loading) {
    return (
      <div className="store-manager-dashboard">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading store operations dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="store-manager-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1><Store size={28} strokeWidth={1.8} style={{ verticalAlign: 'middle', marginRight: '10px' }} />Store Manager Dashboard</h1>
          <p className="subtitle">Create orders and track delivery status</p>
        </div>
        <div className="header-actions">
          <button 
            className="create-order-button"
            onClick={() => setShowCreateOrder(true)}
          >
            + Create New Order
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card primary">
          <div className="kpi-icon"><ClipboardList size={24} /></div>
          <div className="kpi-content">
            <h3>Total Orders</h3>
            <p className="kpi-value">{orders.length}</p>
            <p className="kpi-trend">All time</p>
          </div>
        </div>

        <div className="kpi-card warning">
          <div className="kpi-icon"><Hourglass size={24} /></div>
          <div className="kpi-content">
            <h3>Pending Orders</h3>
            <p className="kpi-value">
              {orders.filter(o => o.status === 'pending').length}
            </p>
            <p className="kpi-trend">Awaiting processing</p>
          </div>
        </div>

        <div className="kpi-card info">
          <div className="kpi-icon"><Truck size={24} /></div>
          <div className="kpi-content">
            <h3>In Transit</h3>
            <p className="kpi-value">
              {orders.filter(o => o.status === 'shipped').length}
            </p>
            <p className="kpi-trend">On the way</p>
          </div>
        </div>

        <div className="kpi-card success">
          <div className="kpi-icon"><CheckCircle2 size={24} /></div>
          <div className="kpi-content">
            <h3>Delivered</h3>
            <p className="kpi-value">
              {orders.filter(o => o.status === 'delivered').length}
            </p>
            <p className="kpi-trend positive">Completed</p>
          </div>
        </div>
      </div>

      {/* Create Order Modal */}
      {showCreateOrder && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Create New Order</h2>
              <button 
                className="close-button"
                onClick={() => setShowCreateOrder(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleCreateOrder} className="order-form">
              <div className="form-group">
                <label>Product SKU</label>
                <select
                  value={newOrder.sku}
                  onChange={(e) => setNewOrder({...newOrder, sku: e.target.value})}
                  required
                >
                  <option value="">Select a product</option>
                  {products.map(product => (
                    <option key={product.sku} value={product.sku}>
                      {product.name} ({product.sku})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Store</label>
                <select
                  value={newOrder.store_id}
                  onChange={(e) => setNewOrder({...newOrder, store_id: e.target.value})}
                  required
                >
                  <option value="">Select a store</option>
                  {stores.map(store => (
                    <option key={store.store_id} value={store.store_id}>
                      {store.name} ({store.store_id})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  value={newOrder.quantity}
                  onChange={(e) => setNewOrder({...newOrder, quantity: parseInt(e.target.value)})}
                  min="1"
                  required
                />
              </div>
              <div className="form-actions">
                <button 
                  type="button"
                  className="cancel-button"
                  onClick={() => setShowCreateOrder(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="submit-button">
                  Create Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Orders Table */}
      <div className="orders-section">
        <div className="section-header">
          <h3><Package size={18} style={{ verticalAlign: 'middle', marginRight: '8px' }} />Your Orders</h3>
          <span className="badge">{orders.length} orders</span>
        </div>
        <div className="orders-table">
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Product</th>
                <th>Store</th>
                <th>Quantity</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 20).map((order) => (
                <tr key={order.order_id}>
                  <td className="order-id">{order.order_id}</td>
                  <td>{order.sku}</td>
                  <td>{order.store_id}</td>
                  <td>{order.quantity}</td>
                  <td>
                    <span className={`status-badge ${order.status}`}>
                      {order.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default StoreManagerDashboard;
