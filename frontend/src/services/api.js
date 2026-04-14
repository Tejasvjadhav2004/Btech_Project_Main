import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getInventory = async () => {
  // Let's use warehouse-stock endpoint for general inventory overview
  const response = await api.get('/api/dashboard/warehouse-stock');
  return response.data;
};

// Also an endpoint for products list
export const getProductsList = async () => {
  const response = await api.get('/api/products?limit=100');
  return response.data;
};

// Get detailed inventory data with stock levels
export const getInventoryWithStock = async () => {
  try {
    const response = await api.get('/api/inventory?limit=500');
    return response.data;
  } catch (e) {
    return [];
  }
};

// Assuming there is a forecast endpoint based on requirements
export const getForecast = async () => {
  try {
    const response = await api.get('/api/forecast');
    return response.data;
  } catch (err) {
    // Return dummy data if endpoint doesn't exist yet
    return [
      { id: 1, month: 'Jan', predicted: 1500, actual: 1450 },
      { id: 2, month: 'Feb', predicted: 1600, actual: 1620 },
      { id: 3, month: 'Mar', predicted: 1400, actual: 1380 },
    ];
  }
};

export const getAlerts = async () => {
  const response = await api.get('/api/signals/alerts?acknowledged=false&limit=50');
  return response.data;
};

export const fetchOrders = async () => {
  const response = await api.get('/api/orders?limit=100');
  return response.data;
};

export const triggerOrder = async (sku, store_id, quantity = 10) => {
  const response = await api.post('/api/orders/create', { sku, store_id, quantity, priority: "normal" });
  return response.data;
};

export const getLogs = async () => {
  const response = await api.get('/api/orders/executions/recent?limit=50');
  return response.data;
};

export const getDashboardOverview = async () => {
  const response = await api.get('/api/dashboard/overview');
  return response.data;
};

// Additional dashboard endpoints for detailed analytics
export const getDashboardProductStock = async () => {
  try {
    const response = await api.get('/api/dashboard/product-stock');
    return response.data;
  } catch (e) {
    return [];
  }
};

export const getDashboardWarehouseStock = async () => {
  try {
    const response = await api.get('/api/dashboard/warehouse-stock');
    return response.data;
  } catch (e) {
    return [];
  }
};

export const getDashboardStoreStock = async () => {
  try {
    const response = await api.get('/api/dashboard/store-stock');
    return response.data;
  } catch (e) {
    return [];
  }
};

export const getDashboardLowStock = async () => {
  try {
    const response = await api.get('/api/dashboard/low-stock');
    return response.data;
  } catch (e) {
    return [];
  }
};

export const getDashboardMetrics = async () => {
  try {
    const response = await api.get('/api/dashboard/metrics');
    return response.data;
  } catch (e) {
    return {};
  }
};

// Intelligence Endpoints
export const getSignalStats = async () => {
  try {
    const response = await api.get('/api/signals/stats');
    return response.data;
  } catch (e) {
    return null;
  }
};

export const getActiveSignals = async () => {
  try {
    const response = await api.get('/api/signals/active');
    return response.data;
  } catch (e) {
    return { signals: [] };
  }
};

export const getSchedulerStatus = async () => {
  try {
    const response = await api.get('/api/signals/scheduler/status');
    return response.data;
  } catch (e) {
    return null;
  }
};

export const runDetection = async (type) => {
  const response = await api.post(`/api/signals/detect/${type}`);
  return response.data;
};

export const runAllDetections = async () => {
  const response = await api.post('/api/signals/detect/all');
  return response.data;
};

export const startScheduler = async () => {
  const response = await api.post('/api/signals/scheduler/start');
  return response.data;
};

export const stopScheduler = async () => {
  const response = await api.post('/api/signals/scheduler/stop');
  return response.data;
};

export const acknowledgeSignal = async (signalId) => {
  const response = await api.post(`/api/signals/${signalId}/acknowledge`);
  return response.data;
};

export const resolveSignal = async (signalId) => {
  const response = await api.post(`/api/signals/${signalId}/resolve`);
  return response.data;
};

// Deliveries
export const getDeliveries = async (limit = 100, status = null) => {
  const params = new URLSearchParams({ limit });
  if (status && status !== 'All') params.append('status', status.toLowerCase());
  const response = await api.get(`/api/deliveries?${params.toString()}`);
  return response.data;
};

export const startDelivery = async (id) => {
  const response = await api.post(`/api/deliveries/${id}/start`);
  return response.data;
};

export const completeDelivery = async (id) => {
  const response = await api.post(`/api/deliveries/${id}/complete`);
  return response.data;
};

// Warehouses
export const getWarehouses = async () => {
  const response = await api.get('/api/warehouses');
  return response.data;
};

// Stores
export const getStores = async () => {
  const response = await api.get('/api/stores');
  return response.data;
};

// Replenishment Orders
export const getReplenishmentOrders = async () => {
  const response = await api.get('/api/signals/replenishment-orders');
  return response.data;
};

export const approveReplenishmentOrder = async (id) => {
  const response = await api.post(`/api/signals/replenishment-orders/${id}/approve`);
  return response.data;
};
