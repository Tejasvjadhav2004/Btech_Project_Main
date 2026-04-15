# Supply Chain Management System 

A comprehensive Supply Chain Management (SCM) system built with Python, MongoDB, FastAPI, and React. This system serves as the foundation for a multi-agent AI orchestration platform, designed to be scalable and production-ready with advanced sensing and intelligence capabilities.

## 🎯Objectives

✅ Initialize multi-warehouse + multi-store system  
✅ Load and transform real datasets (fashion + supply chain)  
✅ Store data in MongoDB with optimized schemas  
✅ Provide backend APIs using FastAPI  
✅ Build interactive monitoring dashboard with React  
✅ Implement order simulation and inventory tracking  
✅ Design for future AI/agent layer integration  
✅ **NEW: Implement intelligence layer with signal detection**  
✅ **NEW: Add automated monitoring and alerting system**  
✅ **NEW: Implement forecasting capabilities**  
✅ **NEW: Add delivery management and tracking**  

## 🏗️ System Architecture

```
CSV Datasets → Data Transform → MongoDB → FastAPI → Monitoring Engine → React Dashboard
                                         ↓
                              Intelligence Layer
                                         ↓
                              Signal Detection & Alerts
```

## 📁 Project Structure

```
supply-chain-management/
├── backend/
│   ├── api/                    # FastAPI application
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── config.py          # Application settings
│   │   ├── models/            # Pydantic models
│   │   └── routers/           # API route handlers
│   │       ├── products.py    # Product endpoints
│   │       ├── warehouses.py  # Warehouse endpoints
│   │       ├── stores.py      # Store endpoints
│   │       ├── inventory.py   # Inventory endpoints
│   │       ├── dashboard.py   # Dashboard endpoints
│   │       ├── orders.py      # Order endpoints
│   │       ├── deliveries.py  # Delivery endpoints
│   │       ├── signals.py     # Signal detection endpoints
│   │       └── forecast.py    # Forecasting endpoints
│   ├── db/                    # Database layer
│   │   ├── connection.py      # MongoDB connection manager
│   │   └── collections.py     # Intelligence collections setup
│   ├── services/              # Business logic layer
│   │   ├── monitoring_service.py
│   │   ├── order_service.py
│   │   ├── inventory_service.py
│   │   ├── analytics_service.py
│   │   ├── decision_service.py
│   │   ├── delivery_service.py
│   │   ├── execution_logger.py
│   │   └── scheduler_service.py
│   ├── scripts/               # Data processing scripts
│   │   ├── data_loader.py
│   │   ├── data_transformer.py
│   │   ├── data_generator.py
│   │   ├── mongo_initializer.py
│   │   ├── seed_data.py
│   │   └── example_scenario.py
│   ├── data/                  # CSV datasets
│   │   ├── raw/
│   │   │   ├── supply_chain_data.csv
│   │   │   └── fashion_boutique_dataset.csv
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── pages/            # React pages
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Inventory.jsx
│   │   │   ├── Alerts.jsx
│   │   │   ├── Intelligence.jsx
│   │   │   ├── Orders.jsx
│   │   │   ├── Deliveries.jsx
│   │   │   ├── Forecast.jsx
│   │   │   ├── Logs.jsx
│   │   │   ├── Warehouses.jsx
│   │   │   └── Stores.jsx
│   │   ├── services/         # API service layer
│   │   │   └── api.js
│   │   ├── components/       # Reusable components
│   │   │   ├── Layout.jsx
│   │   │   └── Sidebar.jsx
│   │   └── hooks/            # Custom React hooks
│   │       └── usePolling.js
│   ├── public/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- MongoDB Atlas account with a configured cluster
- Node.js 16+ and npm for React frontend

### Installation

1. **Configure MongoDB Atlas**
   ```bash
   cp backend/.env.example backend/.env
   ```
   Update `.env` with your MongoDB Atlas connection string:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
   MONGODB_DATABASE_NAME=supply_chain_db
   ```

2. **Install backend dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Place data files** in the `backend/data/raw/` directory:
   - `supply_chain_data.csv`
   - `fashion_boutique_dataset.csv`

4. **Seed the database**
   ```bash
   python backend/scripts/seed_data.py
   ```

5. **Start the applications**
   
   **Terminal 1 - FastAPI Backend:**
   ```bash
   uvicorn backend.api.main:app --reload
   ```
   
   **Terminal 2 - React Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Access Your System
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

## 📊 API Endpoints

### Core APIs (10 endpoints)
- `GET /api/products` - List all products (with pagination)
- `GET /api/products/{sku}` - Get product by SKU
- `GET /api/warehouses` - List all warehouses
- `GET /api/warehouses/{warehouse_id}` - Get warehouse details
- `GET /api/warehouses/{warehouse_id}/inventory` - Get warehouse inventory
- `GET /api/stores` - List all stores
- `GET /api/stores/{store_id}` - Get store details
- `GET /api/stores/{store_id}/inventory` - Get store inventory
- `GET /api/inventory` - List all inventory items (with filters)
- `POST /api/orders` - Create new order

### Dashboard APIs (6 endpoints)
- `GET /api/dashboard/overview` - System KPIs
- `GET /api/dashboard/product-stock` - Stock distribution by product
- `GET /api/dashboard/warehouse-stock` - Stock by warehouse
- `GET /api/dashboard/store-stock` - Stock by store
- `GET /api/dashboard/low-stock` - Low stock alerts
- `GET /api/dashboard/metrics` - Detailed metrics with alerts

### Order APIs (3 endpoints)
- `GET /api/orders/{order_id}` - Get order by ID
- `GET /api/orders` - List orders (with filters)
- `PUT /api/orders/{order_id}/status` - Update order status

### Delivery APIs (5 endpoints)
- `GET /api/deliveries` - List all deliveries
- `GET /api/deliveries/{delivery_id}` - Get delivery details
- `POST /api/deliveries/{delivery_id}/start` - Start delivery
- `POST /api/deliveries/{delivery_id}/complete` - Complete delivery
- `GET /api/orders/executions/recent` - Get recent execution logs

### Signal/Intelligence APIs (10+ endpoints)
- `GET /api/signals/alerts` - Get all alerts
- `GET /api/signals/stats` - Get signal statistics
- `GET /api/signals/active` - Get active signals
- `POST /api/signals/detect/{type}` - Run specific detection
- `POST /api/signals/detect/all` - Run all detections
- `GET /api/signals/scheduler/status` - Get scheduler status
- `POST /api/signals/scheduler/start` - Start scheduler
- `POST /api/signals/scheduler/stop` - Stop scheduler
- `POST /api/signals/{signalId}/acknowledge` - Acknowledge signal
- `POST /api/signals/{signalId}/resolve` - Resolve signal
- `GET /api/signals/replenishment-orders` - Get replenishment orders
- `POST /api/signals/replenishment-orders/{id}/approve` - Approve replenishment

### Forecasting APIs (2+ endpoints)
- `GET /api/forecast` - Get demand forecast
- `POST /api/forecast/generate` - Generate new forecast

**Total: 35+ API endpoints**

## 🎨 Frontend Features

### React Pages (10 pages)
1. **Dashboard** 📊 - KPI cards, stock distribution charts, top products, real-time metrics
2. **Inventory** 📦 - Inventory management with tables, filters, and stock levels
3. **Alerts** 🚨 - Low stock warnings with severity levels, signal acknowledgment
4. **Intelligence** 🧠 - AI-powered insights, signal detection, scheduler control
5. **Orders** 🛒 - Order management, creation, and tracking
6. **Deliveries** 🚚 - Delivery tracking, status management
7. **Forecast** 📈 - Demand forecasting and predictions
8. **Logs** 📋 - Execution logs and system events
9. **Warehouses** 🏭 - Warehouse inventory and utilization
10. **Stores** 🏪 - Store inventory and performance

### Key Features
- **Real-time Updates**: Polling mechanism for live data
- **Interactive Charts**: Visual analytics with Plotly
- **Signal Management**: Alert acknowledgment and resolution
- **Scheduler Control**: Start/stop automated monitoring
- **Responsive Design**: Works on desktop and mobile

## 🗄️ MongoDB Schema

### Collections with Indexes

| Collection | Purpose | Documents | Indexes |
|------------|---------|-----------|---------|
| products | Product catalog | 100+ | sku, category, brand |
| warehouses | Warehouse locations | 5+ | warehouse_id, location.city |
| stores | Store locations | 8+ | store_id, location.city |
| inventory | Stock levels | 800+ | sku, location_id, location_type |
| suppliers | Supplier information | 10+ | supplier_id |
| orders | Order records | Dynamic | order_id, store_id, status |
| deliveries | Delivery tracking | Dynamic | delivery_id, order_id |
| signals | Intelligence signals | Dynamic | signal_id, type, severity |
| replenishment_orders | Auto-generated orders | Dynamic | order_id, status |
| execution_logs | System events | Dynamic | timestamp, event_type |

### Key Schema Elements

**products**: sku, name, category, brand, prices, sales data, AI fields (demand_forecast, optimization_score, tags)  
**warehouses**: warehouse_id, name, location, capacity, utilization, AI fields (efficiency_metrics)  
**stores**: store_id, name, location, capacity, utilization, AI fields (customer_metrics)  
**inventory**: sku, location_id, location_type, quantities, reorder_level, AI fields (stock_velocity)  
**signals**: signal_id, type, severity, data, timestamp, acknowledged, resolved  
**deliveries**: delivery_id, order_id, source, destination, status, tracking, ai_optimization  

## 🔧 Configuration

### Environment Variables

```env
# MongoDB Configuration (MongoDB Atlas)
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/
MONGODB_DATABASE_NAME=supply_chain_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True

# Business Configuration
LOW_STOCK_THRESHOLD=20
NUM_WAREHOUSES=5
NUM_STORES=8
WAREHOUSE_CITIES=["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"]
STORE_CITIES=["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad"]

# Intelligence Configuration
SIGNAL_DETECTION_INTERVAL=300  # seconds
SCHEDULER_ENABLED=true
```

## 📈 System Capabilities

### Data Processing
- Load CSV datasets (supply chain + fashion)
- Validate and transform data
- Generate synthetic warehouses and stores
- Create realistic inventory distribution
- Establish MongoDB indexes

### Monitoring & Analytics
- Real-time KPI tracking
- Stock distribution analysis
- Low stock detection (configurable threshold)
- Warehouse utilization monitoring
- Category-wise stock analysis
- Top product identification

### Order Management
- Order creation and validation
- Inventory availability checking
- Stock reservation and updates
- Order status tracking
- Fulfillment source assignment

### Delivery Management
- Delivery creation and tracking
- Status updates (pending, in_transit, delivered)
- Route optimization
- Real-time tracking

### Intelligence Layer
- **Signal Detection**: Automated monitoring of critical events
- **Alert System**: Severity-based alerts (critical, warning, info)
- **Scheduler**: Background tasks for periodic checks
- **Decision Engine**: AI-powered recommendations
- **Execution Logging**: Track all system events

### Forecasting
- Demand prediction using historical data
- Seasonal trend analysis
- Inventory optimization recommendations
- Replenishment order generation

## 🎯 Expected Data After Seeding

| Entity | Count | Details |
|--------|-------|---------|
| Products | 100+ | From fashion dataset |
| Warehouses | 5+ | Major Indian cities |
| Stores | 8+ | Across 8 cities |
| Suppliers | 10+ | From dataset |
| Inventory Records | 800+ | Multi-location stock |
| Total Stock Units | 15,000+ | High in WH, low in stores |

### Stock Distribution
- **Warehouses**: ~80% of total stock (high capacity)
- **Stores**: ~20% of total stock (quick access)
- **Low Stock Alerts**: 5-10 items initially

## 🔧 Technical Highlights

### Architecture Patterns
- **Singleton Pattern** - Database connection management
- **Dependency Injection** - FastAPI database access
- **Separation of Concerns** - Clear layer boundaries
- **Repository Pattern** - Data access abstraction
- **Observer Pattern** - Signal detection and alerting

### Performance Optimizations
- **MongoDB Indexes** - Unique and compound indexes
- **Aggregation Pipelines** - Efficient complex queries
- **Pydantic Validation** - Fast data validation
- **Async Ready** - FastAPI async support
- **Background Scheduler** - Automated monitoring

### Future-Ready Design
- **AI/ML Fields** - Reserved for demand forecasting, optimization
- **Agent Hooks** - Ready for autonomous agents
- **Scalable Schema** - Easy to extend
- **Modular Structure** - Easy to add features
- **Intelligence Layer** - Foundation for AI integration

## 🧪 Test the System

### API Examples

```bash
# Health check with scheduler status
curl http://localhost:8000/health

# Get all products
curl http://localhost:8000/api/products

# Get dashboard overview
curl http://localhost:8000/api/dashboard/overview

# Get low stock alerts
curl http://localhost:8000/api/signals/alerts?acknowledged=false

# Get signal statistics
curl http://localhost:8000/api/signals/stats

# Run all detections manually
curl -X POST http://localhost:8000/api/signals/detect/all

# Create a test order
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "ST001",
    "items": [{"sku": "SKU-001", "quantity": 5}]
  }'

# Get delivery status
curl http://localhost:8000/api/deliveries?limit=10

# Get forecast
curl http://localhost:8000/api/forecast
```

### Frontend Testing
1. Navigate to http://localhost:3000
2. Explore all 10 pages
3. Test signal acknowledgment in Alerts page
4. Run manual detections in Intelligence page
5. Create orders and track deliveries
6. View real-time updates with polling

## 🔍 Troubleshooting

### Can't connect to MongoDB
1. Verify your MongoDB Atlas cluster is running
2. Check your `.env` file has correct `MONGODB_URI` connection string
3. Ensure your IP address is whitelisted in MongoDB Atlas
4. Verify your MongoDB Atlas credentials are correct

### Frontend shows no data
1. Make sure you ran the seed script: `python backend/scripts/seed_data.py`
2. Check the seed script output for errors
3. Verify data in your MongoDB Atlas dashboard
4. Ensure the FastAPI backend is running on http://localhost:8000

### Signals not detecting
1. Check scheduler status: `curl http://localhost:8000/api/signals/scheduler/status`
2. Verify scheduler is running and has jobs
3. Check execution logs for errors
4. Manually trigger detection: `curl -X POST http://localhost:8000/api/signals/detect/all`

### API returns errors
1. Check the terminal where uvicorn is running for error messages
2. Verify all dependencies are installed: `pip list`
3. Check your `.env` file is configured correctly

## 🎓 What's Next?

### Phase 4: Advanced AI Integration (Future)
- Machine learning models for demand prediction
- Reinforcement learning for inventory optimization
- Natural language processing for supplier communication
- Computer vision for quality control

### Phase 5: Multi-Agent System (Future)
- Autonomous inventory management agents
- Order fulfillment agents
- Supplier coordination agents
- Demand prediction agents
- Route optimization agents

### Phase 6: Enterprise Features (Future)
- Multi-tenant support
- Role-based access control
- Audit logging
- Advanced reporting
- Integration with ERP systems

## ✅ Success Criteria Met

✅ MongoDB running and seeded with data  
✅ All API endpoints implemented and functional  
✅ React frontend displays KPIs and charts correctly  
✅ Low stock alerts detected and shown  
✅ Orders can be created and inventory updates  
✅ Intelligence layer with signal detection working  
✅ Background scheduler for automated monitoring  
✅ Delivery management and tracking  
✅ Forecasting capabilities  
✅ System is scalable for future AI/agent integration  
✅ Complete documentation provided  


The Supply Chain Management System is now ready for:
1. **Testing** - Verify all functionality works as expected
2. **Demonstration** - Show stakeholders the system
3. **Scaling** - Add more products, warehouses, stores
4. **Integration** - Connect to real systems
5. **Next Phase** - Begin advanced AI integration

---

**Built with ❤️ for the Multi-Agent AI System for Supply Chain Management Orchestration**
**Version 3.0.0 - Sensing & Intelligence Layer**
