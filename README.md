# Supply Chain Management System - Phase 1

## Industry Initialization + Monitoring System

A comprehensive Supply Chain Management (SCM) system built with Python, MongoDB, FastAPI, and Streamlit. This system serves as the foundation for a multi-agent AI orchestration platform, designed to be scalable and production-ready.

## 🎯 Phase 1 Objectives

Phase 1 focuses on building the core infrastructure and monitoring capabilities:

- ✅ Initialize multi-warehouse + multi-store system
- ✅ Load and transform real datasets (fashion + supply chain)
- ✅ Store data in MongoDB with optimized schemas
- ✅ Provide backend APIs using FastAPI
- ✅ Build interactive monitoring dashboard with Streamlit
- ✅ Implement order simulation and inventory tracking
- ✅ Design for future AI/agent layer integration

## 🏗️ System Architecture

```
┌─────────────────┐
│   CSV Datasets  │
│  (Fashion + SCM)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Transform  │
│    Pipeline     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    MongoDB      │
│   (7 Collections)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    FastAPI      │
│   (REST APIs)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Monitoring      │
│    Engine       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit      │
│   Dashboard     │
└─────────────────┘
```

## 📁 Project Structure

```
supply-chain-management/
│
├── api/                          # FastAPI application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Application settings
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── product.py
│   │   ├── warehouse.py
│   │   ├── store.py
│   │   ├── inventory.py
│   │   ├── supplier.py
│   │   └── order.py
│   └── routers/                  # API route handlers
│       ├── __init__.py
│       ├── products.py
│       ├── warehouses.py
│       ├── stores.py
│       ├── inventory.py
│       ├── dashboard.py
│       └── orders.py
│
├── db/                           # Database layer
│   ├── __init__.py
│   └── connection.py             # MongoDB connection manager
│
├── services/                     # Business logic layer
│   ├── __init__.py
│   ├── monitoring_service.py     # Stock monitoring & KPIs
│   ├── order_service.py          # Order management
│   ├── inventory_service.py      # Inventory operations
│   └── analytics_service.py      # Advanced analytics
│
├── scripts/                      # Data processing scripts
│   ├── data_loader.py            # CSV data loading
│   ├── data_transformer.py       # Data transformation
│   ├── data_generator.py         # Synthetic data generation
│   ├── mongo_initializer.py      # MongoDB initialization
│   └── seed_data.py              # Main seeding script
│
├── dashboard/                    # Streamlit dashboard
│   ├── __init__.py
│   └── app.py                    # Dashboard application
│
├── data/                         # Data files
│   ├── supply_chain_data.csv     # Supply chain dataset
│   └── fashion_boutique_dataset.csv  # Fashion dataset
│
├── plans/                        # Documentation
│   └── phase1_architect_plan.md  # Architect plan
│
├── .env                          # Environment variables (create from .env.example)
├── .env.example                  # Environment variable template
├── docker-compose.yml            # Docker services (MongoDB)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- MongoDB (via Docker)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd supply-chain-management
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MongoDB with Docker**
   ```bash
   docker-compose up -d
   ```
   
   This starts:
   - MongoDB on port 27017
   - MongoDB Express on port 8081 (web UI at http://localhost:8081)
   
   Default credentials:
   - Username: `admin`
   - Password: `admin123`

5. **Configure environment variables**
   
   Copy `.env.example` to `.env` and edit if needed:
   ```bash
   cp .env.example .env
   ```
   
   Default configuration:
   ```env
   MONGODB_URI=mongodb://admin:admin123@localhost:27017/
   MONGODB_DATABASE_NAME=supply_chain_db
   ```
   
   All other settings use sensible defaults.

6. **Seed the database**
   
   Place your CSV files in the `data/` directory:
   - `supply_chain_data.csv`
   - `fashion_boutique_dataset.csv`
   
   Then run:
   ```bash
   python scripts/seed_data.py
   ```
   
   This will:
   - Load and validate CSV data
   - Transform data to MongoDB schema
   - Generate 5 warehouses and 8 stores
   - Generate inventory data (high stock for warehouses, low stock for stores)
   - Create indexes for optimal performance
   
   Output:
   - 100+ products from fashion dataset
   - 5 warehouses in major Indian cities
   - 8 stores across 8 cities
   - Inventory with proper stock distribution

7. **Start the FastAPI backend**
   ```bash
   # Option 1: Using uvicorn directly
   uvicorn api.main:app --reload
   
   # Option 2: Using python
   python -m uvicorn api.main:app --reload
   ```
   
   The API will be available at:
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

8. **Start the Streamlit dashboard**
   
   In a new terminal:
   ```bash
   streamlit run dashboard/app.py
   ```
   
   The dashboard will be available at:
   - Dashboard: http://localhost:8501

## 📊 API Endpoints

### Core APIs

#### Products
- `GET /api/products` - List all products (with pagination)
- `GET /api/products/{sku}` - Get product by SKU

#### Warehouses
- `GET /api/warehouses` - List all warehouses
- `GET /api/warehouses/{warehouse_id}` - Get warehouse details
- `GET /api/warehouses/{warehouse_id}/inventory` - Get warehouse inventory

#### Stores
- `GET /api/stores` - List all stores
- `GET /api/stores/{store_id}` - Get store details
- `GET /api/stores/{store_id}/inventory` - Get store inventory

#### Inventory
- `GET /api/inventory` - List all inventory items (with filters)
  - Query params: `sku`, `location_id`, `location_type` (warehouse/store), `threshold`

### Dashboard APIs

- `GET /api/dashboard/overview` - System KPIs
  ```json
  {
    "total_products": 100,
    "total_stock": 15000,
    "low_stock_alerts": 5,
    "warehouse_utilization": 65.5,
    "total_revenue": 250000.00
  }
  ```

- `GET /api/dashboard/product-stock` - Stock distribution by product
- `GET /api/dashboard/warehouse-stock` - Stock by warehouse
- `GET /api/dashboard/store-stock` - Stock by store
- `GET /api/dashboard/low-stock` - Low stock alerts (threshold query param)
- `GET /api/dashboard/metrics` - Detailed metrics with alerts

### Order APIs

- `POST /api/orders` - Create new order
  ```json
  {
    "store_id": "STORE-001",
    "items": [
      {
        "sku": "SKU-001",
        "quantity": 5
      }
    ]
  }
  ```

- `GET /api/orders/{order_id}` - Get order by ID
- `GET /api/orders` - List orders (with filters)
  - Query params: `store_id`, `status`, `limit`
- `PUT /api/orders/{order_id}/status` - Update order status

## 🎨 Dashboard Features

### Pages

1. **Overview** 📊
   - KPI cards (Total Products, Stock, Alerts, Utilization, Revenue)
   - Stock distribution by category (pie chart)
   - Top products by revenue (bar chart)

2. **Warehouses** 🏭
   - Warehouse inventory table
   - Utilization rate chart
   - Stock by warehouse chart

3. **Stores** 🏪
   - Store inventory table
   - Stock by store chart

4. **Products** 📦
   - Product catalog with filters (category, brand)
   - Sales by product chart

5. **Alerts** 🚨
   - Low stock alerts with severity (Critical/Warning)
   - System alerts with expandable details

## 🗄️ MongoDB Schema

### Collections

#### products
```python
{
    "_id": ObjectId,
    "sku": str,                    # Unique product identifier
    "name": str,                   # Product name
    "category": str,               # Product category
    "brand": str,                  # Brand name
    "original_price": float,       # Original price
    "current_price": float,        # Current price
    "total_sales": int,            # Total units sold
    "total_revenue": float,        # Total revenue generated
    "demand_forecast": float,      # AI: Demand prediction
    "optimization_score": float,   # AI: Optimization score
    "tags": List[str],             # AI: Tags for ML models
    "created_at": datetime,
    "updated_at": datetime
}
```

#### warehouses
```python
{
    "_id": ObjectId,
    "warehouse_id": str,           # Unique warehouse ID
    "name": str,                   # Warehouse name
    "location": {
        "city": str,
        "state": str,
        "country": str,
        "coordinates": {
            "lat": float,
            "lng": float
        }
    },
    "capacity": int,               # Total capacity
    "current_utilization": int,    # Current stock
    "efficiency_metrics": dict,    # AI: Efficiency metrics
    "created_at": datetime,
    "updated_at": datetime
}
```

#### stores
```python
{
    "_id": ObjectId,
    "store_id": str,               # Unique store ID
    "name": str,                   # Store name
    "location": {
        "city": str,
        "state": str,
        "country": str,
        "coordinates": {
            "lat": float,
            "lng": float
        }
    },
    "capacity": int,               # Total capacity
    "current_utilization": int,    # Current stock
    "customer_metrics": dict,      # AI: Customer behavior metrics
    "created_at": datetime,
    "updated_at": datetime
}
```

#### inventory
```python
{
    "_id": ObjectId,
    "sku": str,                    # Product SKU
    "location_id": str,            # Warehouse/Store ID
    "location_type": str,          # "warehouse" or "store"
    "quantity": int,               # Current quantity
    "reserved_quantity": int,      # Reserved for orders
    "available_quantity": int,     # Available for orders
    "reorder_level": int,          # Reorder threshold
    "lead_time_days": int,         # Replenishment lead time
    "stock_velocity": float,       # AI: Stock movement rate
    "last_restocked": datetime,
    "updated_at": datetime
}
```

#### suppliers
```python
{
    "_id": ObjectId,
    "supplier_id": str,            # Unique supplier ID
    "name": str,                   # Supplier name
    "location": {
        "city": str,
        "country": str
    },
    "contact": {
        "email": str,
        "phone": str
    },
    "performance_metrics": dict,   # AI: Performance metrics
    "created_at": datetime,
    "updated_at": datetime
}
```

#### orders
```python
{
    "_id": ObjectId,
    "order_id": str,               # Unique order ID
    "store_id": str,               # Store placing the order
    "items": List[dict],           # Order items
    "total_amount": float,         # Total order value
    "status": str,                 # pending, processing, completed, cancelled
    "fulfillment": {
        "source": str,             # Fulfillment source
        "tracking_number": str,
        "estimated_delivery": datetime
    },
    "optimization": dict,          # AI: Optimization data
    "created_at": datetime,
    "updated_at": datetime
}
```

#### deliveries
```python
{
    "_id": ObjectId,
    "delivery_id": str,
    "order_id": str,
    "source": str,
    "destination": str,
    "status": str,
    "tracking": dict,
    "ai_optimization": dict,
    "created_at": datetime,
    "updated_at": datetime
}
```

### Indexes

- **products**: `sku` (unique), `category`, `brand`
- **warehouses**: `warehouse_id` (unique), `location.city`
- **stores**: `store_id` (unique), `location.city`
- **inventory**: `sku`, `location_id`, `location_type`, `sku+location_id` (compound)
- **suppliers**: `supplier_id` (unique)
- **orders**: `order_id` (unique), `store_id`, `status`
- **deliveries**: `delivery_id` (unique), `order_id`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://admin:admin123@localhost:27017/
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
```

## 📈 Monitoring Engine

The monitoring service provides:

- **Stock Monitoring**: Track total stock, distribution, and velocity
- **KPI Calculation**: Key performance indicators (revenue, utilization, alerts)
- **Low Stock Detection**: Identify products below threshold
- **Warehouse Utilization**: Monitor capacity usage
- **Category Analysis**: Stock by product category
- **Top Products**: Products by revenue and sales
- **Alert Generation**: Critical and warning alerts

Example usage:

```python
from services.monitoring_service import MonitoringService

# Get system KPIs
kpis = MonitoringService.get_kpis()
print(f"Total Stock: {kpis['total_stock']}")
print(f"Low Stock Alerts: {kpis['low_stock_alerts']}")

# Detect low stock
low_stock = MonitoringService.detect_low_stock(threshold=20)
for item in low_stock:
    print(f"Low stock: {item['sku']} - {item['quantity']} units")

# Get product distribution
distribution = MonitoringService.get_product_distribution("SKU-001")
for loc in distribution:
    print(f"{loc['location_id']}: {loc['quantity']} units")
```

## 🛒 Order Simulation

The order service handles:

- **Order Creation**: Validate and create orders
- **Stock Validation**: Check inventory availability
- **Inventory Updates**: Update stock after order creation
- **Status Tracking**: Track order fulfillment status

Example:

```python
from services.order_service import OrderService

# Create an order
order_data = {
    "store_id": "STORE-001",
    "items": [
        {"sku": "SKU-001", "quantity": 5},
        {"sku": "SKU-002", "quantity": 3}
    ]
}

order = OrderService.create_order(order_data)
print(f"Order created: {order['order_id']}")

# Update order status
updated = OrderService.update_order_status(order['order_id'], "completed")
print(f"Order status: {updated['status']}")
```

## 🧪 Testing

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get products
curl http://localhost:8000/api/products

# Get warehouses
curl http://localhost:8000/api/warehouses

# Get dashboard overview
curl http://localhost:8000/api/dashboard/overview

# Create an order
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"store_id": "STORE-001", "items": [{"sku": "SKU-001", "quantity": 5}]}'
```

### Test with Python

```python
import requests

# Get KPIs
response = requests.get("http://localhost:8000/api/dashboard/overview")
kpis = response.json()
print(kpis)

# Get low stock alerts
response = requests.get("http://localhost:8000/api/dashboard/low-stock?threshold=20")
alerts = response.json()
print(alerts)
```

## 🚢 Docker Services

### MongoDB + MongoDB Express

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f mongodb

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Access MongoDB Express

- URL: http://localhost:8081
- Username: `admin`
- Password: `admin123`

## 📊 Example Data

After seeding, you'll have:

- **100+ Products** from fashion dataset
  - Categories: T-shirts, Jeans, Dresses, Jackets, etc.
  - Brands: Nike, Adidas, etc.
  - Price range: $10 - $200

- **5 Warehouses** in major cities:
  - Mumbai, Delhi, Bangalore, Kolkata, Chennai
  - Capacity: 5000 units each
  - Stock: 100-500 units per product (high)

- **8 Stores** across cities:
  - Mumbai, Delhi, Bangalore, Kolkata, Chennai, Hyderabad, Pune, Ahmedabad
  - Capacity: 1000 units each
  - Stock: 10-50 units per product (low)

- **Inventory Distribution**:
  - Total stock: ~15,000+ units
  - Warehouse stock: ~12,000 units
  - Store stock: ~3,000 units
  - Low stock alerts: ~5-10 items

## 🚀 Future Phases

This Phase 1 system is designed to support future phases:

### Phase 2: AI/ML Integration
- Demand forecasting models
- Inventory optimization
- Price optimization
- Customer behavior analysis

### Phase 3: Multi-Agent System
- Autonomous agents for inventory management
- Order fulfillment agents
- Supplier coordination agents
- Demand prediction agents

### Phase 4: Advanced Features
- Real-time demand prediction
- Automated restocking
- Dynamic pricing
- Route optimization
- Predictive maintenance

## 🤝 Contributing

This is a Phase 1 implementation focusing on infrastructure and monitoring. Future phases will add AI/ML capabilities and multi-agent orchestration.

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern web framework
- MongoDB - Flexible NoSQL database
- Streamlit - Interactive dashboards
- pandas - Data processing

## 📞 Support

For issues or questions:
1. Check the [Architect Plan](plans/phase1_architect_plan.md)
2. Review API docs at `/docs`
3. Check MongoDB logs: `docker-compose logs mongodb`
4. Check API logs in terminal

## 🎯 Success Criteria

Phase 1 is successful when:

- ✅ MongoDB is running and seeded with data
- ✅ All API endpoints return correct data
- ✅ Dashboard displays KPIs and charts correctly
- ✅ Low stock alerts are detected and shown
- ✅ Orders can be created and inventory updates
- ✅ System is scalable for future AI/agent integration

---

**Built for the Multi-Agent AI System for Supply Chain Management Orchestration**
