import React, { useEffect, useState } from 'react';
import { fetchOrders, triggerOrder, processOrder, shipOrder, deliverOrder, cancelOrder, getProductsList, getStores, validateOrder } from '../services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sku, setSku] = useState('');
  const [storeId, setStoreId] = useState('');
  const [quantity, setQuantity] = useState(10);
  const [orderLoad, setOrderLoad] = useState(false);
  const [statusFilter, setStatusFilter] = useState('All');
  const [actionLoading, setActionLoading] = useState({});
  const [products, setProducts] = useState([]);
  const [stores, setStores] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);

  // Order validation state
  const [validation, setValidation] = useState(null);
  const [validating, setValidating] = useState(false);

  const loadOrders = () => {
    setLoading(true);
    fetchOrders(statusFilter === 'All' ? null : statusFilter.toLowerCase())
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
    loadProductsAndStores();
  }, [statusFilter]);

  // Validate order when sku, storeId, or quantity changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (sku && storeId && quantity > 0) {
        validateOrderSelection();
      } else {
        setValidation(null);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [sku, storeId, quantity]);

  const loadProductsAndStores = async () => {
    try {
      const [productsData, storesData] = await Promise.all([
        getProductsList(),
        getStores()
      ]);
      setProducts(productsData || []);
      setStores(storesData || []);
    } catch (err) {
      console.error('Error loading products/stores:', err);
    } finally {
      setDataLoading(false);
    }
  };

  const validateOrderSelection = async () => {
    setValidating(true);
    try {
      const result = await validateOrder(sku, storeId, quantity);
      setValidation(result);
    } catch (err) {
      console.error('Validation error:', err);
      setValidation({ valid: false, errors: ['Validation failed'] });
    } finally {
      setValidating(false);
    }
  };

  const handleCreateOrder = () => {
    if (!sku || !storeId) return alert('Please select Product and Store');

    // Check validation before creating
    if (validation && !validation.can_fulfill) {
      const proceed = window.confirm(
        `Warning: ${validation.warnings?.join(', ') || 'Insufficient stock'}.\n\nDo you want to create the order anyway? It may fail during processing.`
      );
      if (!proceed) return;
    }

    setOrderLoad(true);
    triggerOrder(sku, storeId, quantity)
      .then(() => {
        alert('Order created successfully!');
        setSku('');
        setStoreId('');
        setQuantity(10);
        setValidation(null);
        loadOrders();
      })
      .catch(err => {
        alert('Error creating order: ' + (err.response?.data?.detail || err.message));
        console.error(err);
      })
      .finally(() => setOrderLoad(false));
  };

  const handleOrderAction = async (orderId, action, actionFn) => {
    setActionLoading(prev => ({ ...prev, [`${orderId}-${action}`]: true }));
    try {
      await actionFn(orderId);
      alert(`Order ${action} successfully!`);
      loadOrders();
    } catch (err) {
      alert(`Error ${action} order: ` + (err.response?.data?.detail || err.message));
      console.error(err);
    } finally {
      setActionLoading(prev => ({ ...prev, [`${orderId}-${action}`]: false }));
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { bg: '#fef3c7', color: '#d97706' },
      allocated: { bg: '#e0e7ff', color: '#3730a3' },
      shipped: { bg: '#dbeafe', color: '#1d4ed8' },
      delivered: { bg: '#dcfce3', color: '#166534' },
      cancelled: { bg: '#fee2e2', color: '#dc2626' },
      failed: { bg: '#fee2e2', color: '#991b1b' }
    };
    const style = styles[status?.toLowerCase()] || { bg: '#f1f5f9', color: '#64748b' };
    return (
      <span style={{
        padding: '5px 10px',
        borderRadius: '20px',
        fontSize: '12px',
        fontWeight: 'bold',
        backgroundColor: style.bg,
        color: style.color
      }}>
        {status?.toUpperCase()}
      </span>
    );
  };

  const getActionButtons = (order) => {
    const buttons = [];
    const isLoading = (action) => actionLoading[`${order.order_id}-${action}`];

    if (order.status === 'pending') {
      buttons.push(
        <button
          key="process"
          onClick={() => handleOrderAction(order.order_id, 'process', processOrder)}
          disabled={isLoading('process')}
          style={{
            padding: '6px 12px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isLoading('process') ? 'wait' : 'pointer',
            fontSize: '12px',
            opacity: isLoading('process') ? 0.7 : 1
          }}
        >
          {isLoading('process') ? 'Processing...' : 'Process'}
        </button>
      );
    }

    if (order.status === 'allocated') {
      buttons.push(
        <button
          key="ship"
          onClick={() => handleOrderAction(order.order_id, 'ship', shipOrder)}
          disabled={isLoading('ship')}
          style={{
            padding: '6px 12px',
            backgroundColor: '#8b5cf6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isLoading('ship') ? 'wait' : 'pointer',
            fontSize: '12px',
            opacity: isLoading('ship') ? 0.7 : 1
          }}
        >
          {isLoading('ship') ? 'Shipping...' : 'Ship'}
        </button>
      );
    }

    if (order.status === 'shipped') {
      buttons.push(
        <button
          key="deliver"
          onClick={() => handleOrderAction(order.order_id, 'deliver', deliverOrder)}
          disabled={isLoading('deliver')}
          style={{
            padding: '6px 12px',
            backgroundColor: '#22c55e',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isLoading('deliver') ? 'wait' : 'pointer',
            fontSize: '12px',
            opacity: isLoading('deliver') ? 0.7 : 1
          }}
        >
          {isLoading('deliver') ? 'Delivering...' : 'Deliver'}
        </button>
      );
    }

    if (['pending', 'allocated', 'shipped'].includes(order.status)) {
      buttons.push(
        <button
          key="cancel"
          onClick={() => handleOrderAction(order.order_id, 'cancel', cancelOrder)}
          disabled={isLoading('cancel')}
          style={{
            padding: '6px 12px',
            backgroundColor: '#ef4444',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: isLoading('cancel') ? 'wait' : 'pointer',
            fontSize: '12px',
            marginLeft: '5px',
            opacity: isLoading('cancel') ? 0.7 : 1
          }}
        >
          {isLoading('cancel') ? 'Cancelling...' : 'Cancel'}
        </button>
      );
    }

    return buttons.length > 0 ? buttons : <span style={{ color: '#94a3b8', fontSize: '12px' }}>No actions</span>;
  };

  const orderStatusData = [
    { name: 'Pending', value: orders.filter(o => o.status === 'pending').length, color: '#f59e0b' },
    { name: 'Allocated', value: orders.filter(o => o.status === 'allocated').length, color: '#6366f1' },
    { name: 'Shipped', value: orders.filter(o => o.status === 'shipped').length, color: '#3b82f6' },
    { name: 'Delivered', value: orders.filter(o => o.status === 'delivered').length, color: '#22c55e' },
    { name: 'Cancelled', value: orders.filter(o => o.status === 'cancelled').length, color: '#ef4444' },
    { name: 'Failed', value: orders.filter(o => o.status === 'failed').length, color: '#dc2626' }
  ].filter(d => d.value > 0);

  const orderAmountData = orders.slice(-10).map((order, index) => ({
    name: `Order ${index + 1}`,
    amount: order.total_amount || 0
  }));

  const statusOptions = ['All', 'Pending', 'Allocated', 'Shipped', 'Delivered', 'Cancelled', 'Failed'];

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
        {dataLoading ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>Loading products and stores...</div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '20px' }}>
              <div style={{ flex: 2, minWidth: '200px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Product</label>
                <select
                  value={sku}
                  onChange={(e) => setSku(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1', backgroundColor: 'white' }}
                >
                  <option value="">Select a product...</option>
                  {products.map(product => (
                    <option key={product.sku || product.id} value={product.sku || product.id}>
                      {product.name || product.sku || product.id} ({product.sku || product.id}) - ${product.current_price?.toFixed(2) || '0.00'}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ flex: 2, minWidth: '200px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Store</label>
                <select
                  value={storeId}
                  onChange={(e) => setStoreId(e.target.value)}
                  style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1', backgroundColor: 'white' }}
                >
                  <option value="">Select a store...</option>
                  {stores.map(store => (
                    <option key={store.store_id || store.id} value={store.store_id || store.id}>
                      {store.name || store.store_id || store.id} - {store.city || store.location?.city || ''}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ flex: 1, minWidth: '100px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '14px', color: '#64748b' }}>Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                  style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #cbd5e1' }}
                />
              </div>
              <button
                onClick={handleCreateOrder}
                disabled={orderLoad || !sku || !storeId}
                style={{
                  padding: '10px 20px',
                  backgroundColor: sku && storeId ? '#3b82f6' : '#94a3b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: orderLoad || !sku || !storeId ? 'not-allowed' : 'pointer',
                  height: '40px',
                  fontWeight: 'bold',
                  opacity: orderLoad ? 0.7 : 1,
                  minWidth: '120px'
                }}
              >
                {orderLoad ? 'Creating...' : 'Create Order'}
              </button>
            </div>

            {/* Validation Results */}
            {validating && (
              <div style={{ padding: '15px', backgroundColor: '#f8fafc', borderRadius: '8px', marginBottom: '15px' }}>
                <span style={{ color: '#64748b' }}>Checking inventory...</span>
              </div>
            )}

            {validation && !validating && (
              <div style={{
                padding: '15px',
                backgroundColor: validation.valid ? (validation.can_fulfill ? '#dcfce3' : '#fef3c7') : '#fee2e2',
                borderRadius: '8px',
                marginBottom: '15px',
                border: `1px solid ${validation.valid ? (validation.can_fulfill ? '#22c55e' : '#f59e0b') : '#ef4444'}`
              }}>
                {/* Errors */}
                {validation.errors?.length > 0 && (
                  <div style={{ marginBottom: '10px' }}>
                    {validation.errors.map((err, i) => (
                      <div key={i} style={{ color: '#dc2626', fontWeight: 'bold' }}>⚠️ {err}</div>
                    ))}
                  </div>
                )}

                {/* Product Info */}
                {validation.product && (
                  <div style={{ marginBottom: '10px' }}>
                    <strong style={{ color: '#334155' }}>Product:</strong>{' '}
                    <span style={{ color: '#64748b' }}>{validation.product.name}</span>
                    <span style={{ marginLeft: '10px', color: '#059669', fontWeight: 'bold' }}>
                      ${validation.unit_price?.toFixed(2)} x {quantity} = ${validation.total_amount?.toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Store Info */}
                {validation.store && (
                  <div style={{ marginBottom: '10px' }}>
                    <strong style={{ color: '#334155' }}>Store:</strong>{' '}
                    <span style={{ color: '#64748b' }}>{validation.store.name} ({validation.store.city})</span>
                  </div>
                )}

                {/* Stock Availability */}
                {validation.inventory?.length > 0 && (
                  <div>
                    <strong style={{ color: '#334155' }}>
                      Stock Availability:
                      <span style={{
                        marginLeft: '10px',
                        color: validation.can_fulfill ? '#22c55e' : '#f59e0b'
                      }}>
                        {validation.total_available} units available
                        {validation.can_fulfill ? ' ✓' : ` (need ${quantity})`}
                      </span>
                    </strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px' }}>
                      {validation.inventory.slice(0, 4).map((inv, i) => (
                        <div key={i} style={{
                          padding: '8px 12px',
                          backgroundColor: 'white',
                          borderRadius: '6px',
                          fontSize: '12px',
                          border: inv.can_fulfill ? '2px solid #22c55e' : '1px solid #e2e8f0'
                        }}>
                          <div style={{ fontWeight: 'bold', color: '#334155' }}>{inv.warehouse_id}</div>
                          <div style={{ color: inv.available_stock > 0 ? '#059669' : '#dc2626' }}>
                            Stock: {inv.available_stock} / {inv.total_stock}
                          </div>
                          {inv.can_fulfill && <div style={{ color: '#22c55e', fontSize: '11px' }}>✓ Can fulfill</div>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {validation.warnings?.length > 0 && (
                  <div style={{ marginTop: '10px', color: '#d97706' }}>
                    {validation.warnings.map((warn, i) => (
                      <div key={i}>⚠️ {warn}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <div style={{ backgroundColor: 'white', borderRadius: '10px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px' }}>
          <h3 style={{ color: '#334155' }}>Order History</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <label style={{ fontSize: '14px', color: '#64748b' }}>Filter by Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: '8px 12px',
                borderRadius: '5px',
                border: '1px solid #cbd5e1',
                backgroundColor: 'white',
                cursor: 'pointer'
              }}
            >
              {statusOptions.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <button
              onClick={loadOrders}
              style={{
                padding: '8px 12px',
                backgroundColor: '#64748b',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading orders...</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#f1f5f9', borderBottom: '2px solid #e2e8f0' }}>
                  <th style={{ padding: '15px' }}>Order ID</th>
                  <th style={{ padding: '15px' }}>SKU</th>
                  <th style={{ padding: '15px' }}>Store ID</th>
                  <th style={{ padding: '15px' }}>Quantity</th>
                  <th style={{ padding: '15px' }}>Status</th>
                  <th style={{ padding: '15px' }}>Priority</th>
                  <th style={{ padding: '15px' }}>Amount</th>
                  {/* <th style={{ padding: '15px' }}>Warehouse</th> */}
                  <th style={{ padding: '15px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.order_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '15px', fontWeight: 'bold', fontFamily: 'monospace' }}>{order.order_id}</td>
                    <td style={{ padding: '15px' }}>{order.sku || order.items?.[0]?.sku}</td>
                    <td style={{ padding: '15px' }}>{order.store_id}</td>
                    <td style={{ padding: '15px' }}>{order.quantity || order.items?.[0]?.quantity}</td>
                    <td style={{ padding: '15px' }}>{getStatusBadge(order.status)}</td>
                    <td style={{ padding: '15px' }}>
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        backgroundColor: order.priority === 'high' ? '#fee2e2' : order.priority === 'low' ? '#f1f5f9' : '#e0e7ff',
                        color: order.priority === 'high' ? '#dc2626' : order.priority === 'low' ? '#64748b' : '#4f46e5'
                      }}>
                        {order.priority?.toUpperCase() || 'NORMAL'}
                      </span>
                    </td>
                    <td style={{ padding: '15px' }}>${order.total_amount?.toFixed(2) || '0.00'}</td>
                    {/* <td style={{ padding: '15px' }}>{order.warehouse_id || order.assigned_warehouse || '-'}</td> */}
                    <td style={{ padding: '15px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        {getActionButtons(order)}
                      </div>
                    </td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan="9" style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                      No orders found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;
