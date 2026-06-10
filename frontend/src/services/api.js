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
    console.log('Fetching inventory data...');
    const response = await api.get('/api/inventory?limit=500');
    console.log('Inventory data received:', response.data);
    return response.data;
  } catch (e) {
    console.error('Error fetching inventory data:', e);
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
  const response = await api.get('/api/signals/active?limit=50');
  return response.data.signals || [];
};

export const fetchOrders = async (status = null) => {
  const params = new URLSearchParams({ limit: 100 });
  if (status && status !== 'All') params.append('status', status.toLowerCase());
  const response = await api.get(`/api/orders?${params.toString()}`);
  return response.data;
};

export const triggerOrder = async (sku, store_id, quantity = 10) => {
  const response = await api.post('/api/orders/create', { sku, store_id, quantity, priority: "normal" });
  return response.data;
};

export const validateOrder = async (sku, store_id, quantity) => {
  const response = await api.post('/api/orders/validate', { sku, store_id, quantity });
  return response.data;
};

export const processOrder = async (orderId) => {
  const response = await api.post(`/api/orders/process/${orderId}`);
  return response.data;
};

export const shipOrder = async (orderId) => {
  const response = await api.post(`/api/orders/${orderId}/ship`);
  return response.data;
};

export const deliverOrder = async (orderId) => {
  const response = await api.post(`/api/orders/${orderId}/deliver`);
  return response.data;
};

export const cancelOrder = async (orderId) => {
  const response = await api.post(`/api/orders/${orderId}/cancel`);
  return response.data;
};

export const getOrderStats = async () => {
  const response = await api.get('/api/orders/stats');
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

export const generateDemoSignals = async (count = 20) => {
  const response = await api.post(`/api/signals/demo/generate?count=${count}`);
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

export const resolveSignal = async (signalId, verify = false) => {
  const params = verify ? '?verify=true' : '';
  const response = await api.post(`/api/signals/${signalId}/resolve${params}`);
  return response.data;
};

export const verifySignal = async (signalId) => {
  const response = await api.post(`/api/signals/${signalId}/verify`);
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

// Role Management
export const getAvailableRoles = () => {
  return [
    {
      id: 'BUSINESS',
      name: 'Business Owner',
      description: 'Overview of entire supply chain'
    },
    {
      id: 'WAREHOUSE_MANAGER',
      name: 'Warehouse Manager',
      description: 'Manage warehouse operations'
    },
    {
      id: 'STORE_MANAGER',
      name: 'Store Manager',
      description: 'Manage store inventory'
    },
    {
      id: 'LOGISTICS_MANAGER',
      name: 'Logistics Manager',
      description: 'Manage deliveries and transportation'
    },
    {
      id: 'ADMIN',
      name: 'Administrator',
      description: 'Full system access'
    }
  ];
};

// Predictive Intelligence Endpoints
export const getDemandPredictions = async (sku = null, storeId = null, limit = 100) => {
  try {
    const params = new URLSearchParams({ limit });
    if (sku) params.append('sku', sku);
    if (storeId) params.append('store_id', storeId);
    const response = await api.get(`/api/predictions/demand?${params.toString()}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching demand predictions:', e);
    return [];
  }
};

export const getDemandPredictionForSkuStore = async (sku, storeId, daysAhead = 7) => {
  try {
    const response = await api.get(`/api/predictions/demand/${sku}/${storeId}?days_ahead=${daysAhead}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching prediction:', e);
    return null;
  }
};

export const generateDemandPredictions = async () => {
  const response = await api.post('/api/predictions/demand/generate');
  return response.data;
};

export const getStockoutRisks = async (severity = null, limit = 50) => {
  try {
    const params = new URLSearchParams({ limit });
    if (severity) params.append('severity', severity);
    const response = await api.get(`/api/predictions/stockout-risk?${params.toString()}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching stockout risks:', e);
    return [];
  }
};

export const getDelayRisks = async (severity = null, limit = 50) => {
  try {
    const params = new URLSearchParams({ limit });
    if (severity) params.append('severity', severity);
    const response = await api.get(`/api/predictions/delay-risk?${params.toString()}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching delay risks:', e);
    return [];
  }
};

export const getAllPredictiveRisks = async (severity = null, limit = 100) => {
  try {
    const params = new URLSearchParams({ limit });
    if (severity) params.append('severity', severity);
    const response = await api.get(`/api/predictions/all-risks?${params.toString()}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching predictive risks:', e);
    return [];
  }
};

export const runPredictiveSensing = async () => {
  const response = await api.post('/api/predictions/run-predictive-sensing');
  return response.data;
};

export const getHighDemandItems = async (threshold = 50) => {
  try {
    const response = await api.get(`/api/predictions/high-demand?threshold=${threshold}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching high demand items:', e);
    return [];
  }
};

export const getModelStatus = async () => {
  try {
    const response = await api.get('/api/predictions/model-status');
    return response.data;
  } catch (e) {
    console.error('Error fetching model status:', e);
    return null;
  }
};

export const trainDemandModel = async () => {
  const response = await api.post('/api/predictions/train-model');
  return response.data;
};

// ============================================================
// LLM ORCHESTRATION APIS
// ============================================================

export const getOrchestrationContext = async () => {
  try {
    const response = await api.get('/api/llm-orchestration/context');
    return response.data;
  } catch (e) {
    console.error('Error fetching orchestration context:', e);
    return { success: false, context: {} };
  }
};

export const generateOrchestrationPlan = async (params = {}) => {
  try {
    const response = await api.post('/api/llm-orchestration/plan', {
      dry_run: params.dry_run !== false,
      signal_id: params.signal_id,
      signal_type: params.signal_type,
      entity_id: params.entity_id
    });
    return response.data;
  } catch (e) {
    console.error('Error generating orchestration plan:', e);
    return { success: false, error: e.message };
  }
};

export const executeOrchestrationPlan = async (planId, actions) => {
  try {
    const response = await api.post('/api/llm-orchestration/execute', {
      plan_id: planId,
      actions: actions
    });
    return response.data;
  } catch (e) {
    console.error('Error executing plan:', e);
    return { success: false, error: e.message };
  }
};

export const getOrchestrationHistory = async (limit = 20) => {
  try {
    const response = await api.get(`/api/llm-orchestration/history?limit=${limit}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching orchestration history:', e);
    return { success: false, history: [] };
  }
};

export const getOrchestrationDecision = async (decisionId) => {
  try {
    const response = await api.get(`/api/llm-orchestration/decision/${decisionId}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching decision:', e);
    return { success: false };
  }
};

export const explainDecision = async (decisionId) => {
  try {
    const response = await api.get(`/api/llm-orchestration/explanation/${decisionId}`);
    return response.data;
  } catch (e) {
    console.error('Error getting explanation:', e);
    return { success: false };
  }
};

export const getOrchestrationMetrics = async () => {
  try {
    const response = await api.get('/api/llm-orchestration/metrics');
    return response.data;
  } catch (e) {
    console.error('Error fetching orchestration metrics:', e);
    return { success: false, metrics: {} };
  }
};

export const validateOrchestrationActions = async (actions) => {
  try {
    const response = await api.post('/api/llm-orchestration/validate', actions);
    return response.data;
  } catch (e) {
    console.error('Error validating actions:', e);
    return { success: false };
  }
};

export const runAutonomousPipeline = async (dryRun = true) => {
  try {
    const response = await api.post(`/api/llm-orchestration/pipeline/run?dry_run=${dryRun}`);
    return response.data;
  } catch (e) {
    console.error('Error running autonomous pipeline:', e);
    return { success: false, error: e.message };
  }
};

export const processSignalPipeline = async (signalId) => {
  try {
    const response = await api.post(`/api/llm-orchestration/pipeline/signal/${signalId}`);
    return response.data;
  } catch (e) {
    console.error('Error processing signal pipeline:', e);
    return { success: false, error: e.message };
  }
};

export const getOrchestrationHealth = async () => {
  try {
    const response = await api.get('/api/llm-orchestration/health');
    return response.data;
  } catch (e) {
    console.error('Error checking orchestration health:', e);
    return { status: 'unhealthy', error: e.message };
  }
};

// ============================================================
// DEMO SIMULATION APIS
// ============================================================

export const getDemoStatus = async () => {
  try {
    const response = await api.get('/api/demo/status');
    return response.data;
  } catch (e) {
    console.error('Error fetching demo status:', e);
    return { simulation: { state: { is_running: false } }, metrics: {} };
  }
};

export const startDemoSimulation = async (mode = 'ai_autonomous') => {
  try {
    const response = await api.post(`/api/demo/start?mode=${mode}`);
    return response.data;
  } catch (e) {
    console.error('Error starting demo:', e);
    return { success: false, error: e.message };
  }
};

export const stopDemoSimulation = async () => {
  try {
    const response = await api.post('/api/demo/stop');
    return response.data;
  } catch (e) {
    console.error('Error stopping demo:', e);
    return { success: false, error: e.message };
  }
};

export const setDemoMode = async (mode) => {
  try {
    const response = await api.post(`/api/demo/mode/${mode}`);
    return response.data;
  } catch (e) {
    console.error('Error setting demo mode:', e);
    return { success: false, error: e.message };
  }
};

export const triggerDemoScenario = async (scenario, params = {}) => {
  try {
    const response = await api.post(`/api/demo/scenario/${scenario}`, params);
    return response.data;
  } catch (e) {
    console.error('Error triggering scenario:', e);
    return { success: false, error: e.message };
  }
};

export const getDemoMetrics = async (mode = null) => {
  try {
    const url = mode ? `/api/demo/metrics?mode=${mode}` : '/api/demo/metrics';
    const response = await api.get(url);
    return response.data;
  } catch (e) {
    console.error('Error fetching demo metrics:', e);
    return {};
  }
};

export const getDemoMetricsComparison = async () => {
  try {
    const response = await api.get('/api/demo/metrics/comparison');
    return response.data;
  } catch (e) {
    console.error('Error fetching metrics comparison:', e);
    return {};
  }
};

export const getDemoActivities = async (limit = 50) => {
  try {
    const response = await api.get(`/api/demo/activities?limit=${limit}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching demo activities:', e);
    return { activities: [], count: 0 };
  }
};

export const getDemoScenarios = async () => {
  try {
    const response = await api.get('/api/demo/scenarios');
    return response.data;
  } catch (e) {
    console.error('Error fetching demo scenarios:', e);
    return { scenarios: [] };
  }
};

export const resetDemo = async () => {
  try {
    const response = await api.post('/api/demo/reset');
    return response.data;
  } catch (e) {
    console.error('Error resetting demo:', e);
    return { success: false, error: e.message };
  }
};

export const pauseDemoSimulation = async () => {
  try {
    const response = await api.post('/api/demo/pause');
    return response.data;
  } catch (e) {
    console.error('Error pausing demo:', e);
    return { success: false, error: e.message };
  }
};

export const resumeDemoSimulation = async () => {
  try {
    const response = await api.post('/api/demo/resume');
    return response.data;
  } catch (e) {
    console.error('Error resuming demo:', e);
    return { success: false, error: e.message };
  }
};

export const getActivityDetail = async (activityId) => {
  try {
    const response = await api.get(`/api/demo/activities/${activityId}`);
    return response.data;
  } catch (e) {
    console.error('Error fetching activity detail:', e);
    return { success: false };
  }
};

export const getActiveSignalsDetail = async () => {
  try {
    const response = await api.get('/api/demo/signals/active');
    return response.data;
  } catch (e) {
    console.error('Error fetching signals detail:', e);
    return { signals: [], count: 0 };
  }
};

