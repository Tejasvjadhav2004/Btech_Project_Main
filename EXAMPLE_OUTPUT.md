# Example Output - Supply Chain Management System

This document demonstrates the Supply Chain Management System with a simplified example:
- 2 Warehouses
- 2 Stores
- 2 Products

## 📊 System State

### Products

```json
[
  {
    "_id": "67d3f1a2e4b0c001f2d8e9a1",
    "sku": "SKU-001",
    "name": "Classic Cotton T-Shirt",
    "category": "T-shirts",
    "brand": "Nike",
    "original_price": 45.00,
    "current_price": 36.00,
    "total_sales": 150,
    "total_revenue": 5400.00,
    "demand_forecast": 200,
    "optimization_score": 0.85,
    "tags": ["basics", "high-demand"],
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9a2",
    "sku": "SKU-002",
    "name": "Slim Fit Denim Jeans",
    "category": "Jeans",
    "brand": "Levi's",
    "original_price": 89.00,
    "current_price": 71.20,
    "total_sales": 85,
    "total_revenue": 6052.00,
    "demand_forecast": 120,
    "optimization_score": 0.78,
    "tags": ["denim", "premium"],
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  }
]
```

### Warehouses

```json
[
  {
    "_id": "67d3f1a2e4b0c001f2d8e9b1",
    "warehouse_id": "WH-001",
    "name": "Mumbai Central Warehouse",
    "location": {
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "coordinates": {
        "lat": 19.0760,
        "lng": 72.8777
      }
    },
    "capacity": 5000,
    "current_utilization": 350,
    "efficiency_metrics": {
      "fulfillment_rate": 0.95,
      "turnover_rate": 4.2
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9b2",
    "warehouse_id": "WH-002",
    "name": "Delhi North Warehouse",
    "location": {
      "city": "Delhi",
      "state": "Delhi",
      "country": "India",
      "coordinates": {
        "lat": 28.7041,
        "lng": 77.1025
      }
    },
    "capacity": 5000,
    "current_utilization": 280,
    "efficiency_metrics": {
      "fulfillment_rate": 0.92,
      "turnover_rate": 3.8
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  }
]
```

### Stores

```json
[
  {
    "_id": "67d3f1a2e4b0c001f2d8e9c1",
    "store_id": "STORE-001",
    "name": "Mumbai Fashion Outlet",
    "location": {
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India",
      "coordinates": {
        "lat": 19.0760,
        "lng": 72.8777
      }
    },
    "capacity": 1000,
    "current_utilization": 35,
    "customer_metrics": {
      "avg_purchase_value": 85.00,
      "return_rate": 0.08
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9c2",
    "store_id": "STORE-002",
    "name": "Delhi Premium Store",
    "location": {
      "city": "Delhi",
      "state": "Delhi",
      "country": "India",
      "coordinates": {
        "lat": 28.7041,
        "lng": 77.1025
      }
    },
    "capacity": 1000,
    "current_utilization": 28,
    "customer_metrics": {
      "avg_purchase_value": 125.00,
      "return_rate": 0.05
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  }
]
```

### Inventory Distribution

```json
[
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d1",
    "sku": "SKU-001",
    "location_id": "WH-001",
    "location_type": "warehouse",
    "quantity": 200,
    "reserved_quantity": 15,
    "available_quantity": 185,
    "reorder_level": 50,
    "lead_time_days": 3,
    "stock_velocity": 2.5,
    "last_restocked": "2025-01-18T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d2",
    "sku": "SKU-001",
    "location_id": "WH-002",
    "location_type": "warehouse",
    "quantity": 180,
    "reserved_quantity": 10,
    "available_quantity": 170,
    "reorder_level": 50,
    "lead_time_days": 3,
    "stock_velocity": 2.3,
    "last_restocked": "2025-01-18T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d3",
    "sku": "SKU-001",
    "location_id": "STORE-001",
    "location_type": "store",
    "quantity": 20,
    "reserved_quantity": 5,
    "available_quantity": 15,
    "reorder_level": 20,
    "lead_time_days": 2,
    "stock_velocity": 1.8,
    "last_restocked": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d4",
    "sku": "SKU-001",
    "location_id": "STORE-002",
    "location_type": "store",
    "quantity": 15,
    "reserved_quantity": 3,
    "available_quantity": 12,
    "reorder_level": 20,
    "lead_time_days": 2,
    "stock_velocity": 1.5,
    "last_restocked": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d5",
    "sku": "SKU-002",
    "location_id": "WH-001",
    "location_type": "warehouse",
    "quantity": 150,
    "reserved_quantity": 8,
    "available_quantity": 142,
    "reorder_level": 40,
    "lead_time_days": 4,
    "stock_velocity": 1.9,
    "last_restocked": "2025-01-17T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d6",
    "sku": "SKU-002",
    "location_id": "WH-002",
    "location_type": "warehouse",
    "quantity": 100,
    "reserved_quantity": 5,
    "available_quantity": 95,
    "reorder_level": 40,
    "lead_time_days": 4,
    "stock_velocity": 1.7,
    "last_restocked": "2025-01-17T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d7",
    "sku": "SKU-002",
    "location_id": "STORE-001",
    "location_type": "store",
    "quantity": 15,
    "reserved_quantity": 2,
    "available_quantity": 13,
    "reorder_level": 15,
    "lead_time_days": 3,
    "stock_velocity": 1.2,
    "last_restocked": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  },
  {
    "_id": "67d3f1a2e4b0c001f2d8e9d8",
    "sku": "SKU-002",
    "location_id": "STORE-002",
    "location_type": "store",
    "quantity": 13,
    "reserved_quantity": 2,
    "available_quantity": 11,
    "reorder_level": 15,
    "lead_time_days": 3,
    "stock_velocity": 1.0,
    "last_restocked": "2025-01-19T10:00:00Z",
    "updated_at": "2025-01-20T15:30:00Z"
  }
]
```

## 📈 Stock Distribution Summary

### By Product

| Product (SKU) | Total Stock | Warehouse Stock | Store Stock | Available |
|---------------|-------------|-----------------|-------------|-----------|
| SKU-001 (Classic Cotton T-Shirt) | 415 | 380 | 35 | 382 |
| SKU-002 (Slim Fit Denim Jeans) | 278 | 250 | 28 | 261 |

### By Location

| Location | Type | SKU-001 | SKU-002 | Total |
|----------|------|---------|---------|-------|
| WH-001 (Mumbai) | Warehouse | 200 | 150 | 350 |
| WH-002 (Delhi) | Warehouse | 180 | 100 | 280 |
| STORE-001 (Mumbai) | Store | 20 | 15 | 35 |
| STORE-002 (Delhi) | Store | 15 | 13 | 28 |

## 🎯 Dashboard Output

### Overview Page - KPIs

```
┌─────────────────────────────────────────────────────────────────┐
│                    📊 System Overview                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Total Products    Total Stock    Low Stock    Utilization      │
│  ──────────────    ────────────   ─────────    ───────────      │
│        2              693           2            7.0%            │
│                                                                  │
│  Total Revenue                                                     │
│  ─────────────                                                     │
│  $11,452.00                                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Stock Distribution by Category (Pie Chart)

```
                T-shirts: 415 (60%)
              ┌─────────────────────┐
              │                     │
              │                     │
              │                     │
              │    Jeans: 278 (40%) │
              │                     │
              │                     │
              └─────────────────────┘
```

### Warehouse Utilization

```
┌─────────────────────────────────────────────────────────┐
│  Warehouse Utilization Rate (%)                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  WH-001  ████████████████████████████████████  7.0%     │
│  WH-002  ████████████████████████████████       5.6%     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Stock by Warehouse

```
┌─────────────────────────────────────────────────────────┐
│  Current Stock by Warehouse                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  WH-001  ██████████████████████████████████████  350     │
│  WH-002  ████████████████████████████████            280     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 🚨 Alerts Page - Low Stock Alerts

```
┌─────────────────────────────────────────────────────────────────┐
│                    🚨 Low Stock Alerts                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Product            Location        Quantity    Severity         │
│  ─────────────────  ─────────────   ─────────   ─────────────   │
│  SKU-001            STORE-002       15          ⚠️ Warning      │
│  SKU-002            STORE-001       15          ⚠️ Warning      │
│  SKU-002            STORE-002       13          ⚠️ Warning      │
│                                                                  │
│  Critical Alerts: 0                                              │
│  Warning Alerts: 3                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 📊 API Responses

### GET /api/dashboard/overview

```json
{
  "total_products": 2,
  "total_stock": 693,
  "low_stock_alerts": 3,
  "warehouse_utilization": 7.0,
  "total_revenue": 11452.00,
  "timestamp": "2025-01-20T15:30:00Z"
}
```

### GET /api/dashboard/product-stock

```json
{
  "products": [
    {
      "sku": "SKU-001",
      "name": "Classic Cotton T-Shirt",
      "total_quantity": 415,
      "warehouse_quantity": 380,
      "store_quantity": 35,
      "available_quantity": 382,
      "locations": [
        {
          "location_id": "WH-001",
          "location_type": "warehouse",
          "quantity": 200
        },
        {
          "location_id": "WH-002",
          "location_type": "warehouse",
          "quantity": 180
        },
        {
          "location_id": "STORE-001",
          "location_type": "store",
          "quantity": 20
        },
        {
          "location_id": "STORE-002",
          "location_type": "store",
          "quantity": 15
        }
      ]
    },
    {
      "sku": "SKU-002",
      "name": "Slim Fit Denim Jeans",
      "total_quantity": 278,
      "warehouse_quantity": 250,
      "store_quantity": 28,
      "available_quantity": 261,
      "locations": [
        {
          "location_id": "WH-001",
          "location_type": "warehouse",
          "quantity": 150
        },
        {
          "location_id": "WH-002",
          "location_type": "warehouse",
          "quantity": 100
        },
        {
          "location_id": "STORE-001",
          "location_type": "store",
          "quantity": 15
        },
        {
          "location_id": "STORE-002",
          "location_type": "store",
          "quantity": 13
        }
      ]
    }
  ]
}
```

### GET /api/dashboard/warehouse-stock

```json
{
  "warehouses": [
    {
      "warehouse_id": "WH-001",
      "name": "Mumbai Central Warehouse",
      "location": {
        "city": "Mumbai",
        "state": "Maharashtra"
      },
      "capacity": 5000,
      "current_utilization": 350,
      "utilization_rate": 7.0
    },
    {
      "warehouse_id": "WH-002",
      "name": "Delhi North Warehouse",
      "location": {
        "city": "Delhi",
        "state": "Delhi"
      },
      "capacity": 5000,
      "current_utilization": 280,
      "utilization_rate": 5.6
    }
  ]
}
```

### GET /api/dashboard/low-stock?threshold=20

```json
{
  "count": 3,
  "threshold": 20,
  "items": [
    {
      "sku": "SKU-001",
      "name": "Classic Cotton T-Shirt",
      "location_id": "STORE-002",
      "location_type": "store",
      "quantity": 15,
      "reorder_level": 20,
      "status": "warning"
    },
    {
      "sku": "SKU-002",
      "name": "Slim Fit Denim Jeans",
      "location_id": "STORE-001",
      "location_type": "store",
      "quantity": 15,
      "reorder_level": 15,
      "status": "warning"
    },
    {
      "sku": "SKU-002",
      "name": "Slim Fit Denim Jeans",
      "location_id": "STORE-002",
      "location_type": "store",
      "quantity": 13,
      "reorder_level": 15,
      "status": "warning"
    }
  ]
}
```

## 🛒 Order Simulation

### Create Order

**Request:**
```json
POST /api/orders
{
  "store_id": "STORE-001",
  "items": [
    {
      "sku": "SKU-001",
      "quantity": 5
    },
    {
      "sku": "SKU-002",
      "quantity": 3
    }
  ]
}
```

**Response:**
```json
{
  "order_id": "ORD-20250120-001",
  "store_id": "STORE-001",
  "items": [
    {
      "sku": "SKU-001",
      "quantity": 5,
      "unit_price": 36.00,
      "total": 180.00
    },
    {
      "sku": "SKU-002",
      "quantity": 3,
      "unit_price": 71.20,
      "total": 213.60
    }
  ],
  "total_amount": 393.60,
  "status": "pending",
  "created_at": "2025-01-20T16:00:00Z"
}
```

### Inventory After Order

**SKU-001 at STORE-001:**
- Before: 20 total, 5 reserved, 15 available
- After: 20 total, 10 reserved, 10 available

**SKU-002 at STORE-001:**
- Before: 15 total, 2 reserved, 13 available
- After: 15 total, 5 reserved, 10 available

### Update Order Status

**Request:**
```json
PUT /api/orders/ORD-20250120-001/status
{
  "status": "completed"
}
```

**Response:**
```json
{
  "order_id": "ORD-20250120-001",
  "status": "completed",
  "fulfillment": {
    "source": "WH-001",
    "tracking_number": "TRK-20250120-001",
    "estimated_delivery": "2025-01-22T10:00:00Z"
  },
  "updated_at": "2025-01-20T16:30:00Z"
}
```

### Final Inventory After Order Completion

**SKU-001 at STORE-001:**
- Before: 20 total, 10 reserved, 10 available
- After: 15 total, 0 reserved, 15 available

**SKU-002 at STORE-001:**
- Before: 15 total, 5 reserved, 10 available
- After: 12 total, 0 reserved, 12 available

## 📊 System Metrics After Order

### Updated KPIs

```json
{
  "total_products": 2,
  "total_stock": 687,
  "low_stock_alerts": 3,
  "warehouse_utilization": 7.0,
  "total_revenue": 11845.60,
  "timestamp": "2025-01-20T16:30:00Z"
}
```

### Changes:
- Total Stock: 693 → 687 (-6 units sold)
- Total Revenue: $11,452.00 → $11,845.60 (+$393.60)
- Low Stock Alerts: 3 (unchanged, but SKU-002 at STORE-001 now at reorder level)

## 🎯 Key Insights

1. **Stock Distribution**: Warehouses hold ~92% of stock (630 units), stores hold ~8% (63 units)
2. **Utilization**: Current warehouse utilization is low (7%), indicating plenty of capacity
3. **Low Stock**: 3 items at or below reorder level (all in stores)
4. **Revenue**: Top product by revenue is SKU-002 (Jeans) at $6,052
5. **Sales Velocity**: SKU-001 (T-shirts) sells faster (2.4 units/day) than SKU-002 (Jeans) (1.5 units/day)

## 🚀 Next Steps for Scaling

This example demonstrates the system working with minimal data. In production:

- Scale to 100+ products
- Scale to 5+ warehouses
- Scale to 8+ stores
- Implement real-time order processing
- Add demand forecasting (Phase 2)
- Add autonomous agents (Phase 3)
