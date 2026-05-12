# Frontend Fixes - Complete Guide

## Problem Analysis

The frontend code has multiple issues preventing proper display of live inventory data:

### Issue 1: Incorrect Field Names in Warehouses.jsx
**Problem**: Using `total_capacity` instead of `capacity`
```javascript
// ❌ WRONG
{wh.current_utilization || 0} / {wh.total_capacity || 1000}

// ✅ CORRECT
{wh.current_utilization || 0} / {wh.capacity || 1000}
```

### Issue 2: Incorrect Field Names in Stores.jsx
**Problem**: Using `total_capacity` instead of `capacity`
```javascript
// ❌ WRONG
{store.current_utilization || 0} / {store.total_capacity || 1000}

// ✅ CORRECT
{store.current_utilization || 0} / {store.capacity || 1000}
```

### Issue 3: Missing Live Tracking Fields in Inventory.jsx
**Problem**: Not using `current_stock`, `available_stock`, `reserved_stock`, etc.
```javascript
// ❌ WRONG
stockLevel: inventoryRecord?.quantity || 0,

// ✅ CORRECT
stockLevel: inventoryRecord?.current_stock || 0,
availableStock: inventoryRecord?.available_stock || 0,
reservedStock: inventoryRecord?.reserved_stock || 0,
transactionsCount: inventoryRecord?.transactions_count || 0,
totalSales: inventoryRecord?.total_sales || 0,
```

### Issue 4: Old Field Name in Chart Data
**Problem**: Using `quantity` instead of `current_stock`
```javascript
// ❌ WRONG
existing.stock += item.quantity || 0;

// ✅ CORRECT
existing.stock += item.current_stock || 0;
```

## Backend Model Fields (For Reference)

### Warehouse Model
```python
class WarehouseResponse(BaseModel):
    warehouse_id: str
    name: str
    location: Location
    capacity: int              # ← CORRECT FIELD NAME
    current_utilization: int
    is_active: bool
```

### Store Model
```python
class StoreResponse(BaseModel):
    store_id: str
    name: str
    location: Location
    capacity: int              # ← CORRECT FIELD NAME
    current_utilization: int
    is_active: bool
```

### Inventory Model
```python
class InventoryResponse(BaseModel):
    sku: str
    location_id: str
    location_type: str
    
    # Live tracking fields
    current_stock: int         # ← LIVE STOCK
    available_stock: int       # ← AVAILABLE STOCK
    reserved_stock: int        # ← RESERVED STOCK
    initial_stock: int
    
    # Transaction tracking
    transactions_count: int
    total_sales: int
    total_restock: int
    last_updated: Optional[datetime]
    
    # Legacy field for compatibility
    quantity: int              # ← DEPRECATED (use current_stock)
```

## Files That Need Fixing

### 1. ✅ frontend/src/pages/Warehouses.jsx
- Fixed: Changed `total_capacity` to `capacity`

### 2. ✅ frontend/src/pages/Stores.jsx
- Fixed: Changed `total_capacity` to `capacity`

### 3. ✅ frontend/src/pages/Inventory.jsx
- Fixed: Added live tracking fields (current_stock, available_stock, reserved_stock, etc.)
- Fixed: Updated chart data to use current_stock instead of quantity
- Added: New columns for Available Stock, Reserved Stock, Transactions, Total Sales

## Expected Behavior After Fixes

### Warehouses Page
```
Warehouse ID    Name                Location                   Capacity
WH001           Central Warehouse   Maharashtra, India        ████████░░ 60%
                 95,000 / 150,000 utilized
```

### Stores Page
```
Store ID    Name                    Location                   Capacity
ST001       Fashion Boutique       Maharashtra, India        ██████░░░░ 50%
            7,500 / 15,000 utilized
```

### Inventory Page
```
Product Name          SKU           Warehouse        Current Stock    Available Stock    Reserved Stock    Transactions    Total Sales
Summer Dress         PRD001        WH001            95 units         95 units           0 units          5               5
Winter Jacket        PRD002        WH002            120 units        120 units          0 units          8               8
```

## How to Verify Fixes Work

### 1. Run the Backend Fix Script
```bash
cd backend
python scripts/fix_system.py
```

This will:
- Clear old database
- Re-seed with correct capacities (100K-300K for warehouses, 10K-30K for stores)
- Add live tracking fields to inventory
- Simulate initial orders

### 2. Start the Backend Server
```bash
cd backend
python -m uvicorn api.main:app --reload
```

### 3. Start the Frontend Server
```bash
cd frontend
npm run dev
```

### 4. Test the API Endpoints

#### Test Warehouses API
```bash
curl http://localhost:8000/api/warehouses
```

Expected response:
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "warehouse_id": "WH001",
    "name": "Central Warehouse",
    "location": {
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India"
    },
    "capacity": 150000,
    "current_utilization": 95000,
    "is_active": true
  }
]
```

#### Test Stores API
```bash
curl http://localhost:8000/api/stores
```

Expected response:
```json
[
  {
    "id": "507f1f77bcf86cd799439012",
    "store_id": "ST001",
    "name": "Fashion Boutique",
    "location": {
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India"
    },
    "capacity": 15000,
    "current_utilization": 7500,
    "is_active": true
  }
]
```

#### Test Inventory API
```bash
curl http://localhost:8000/api/inventory?limit=5
```

Expected response:
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "sku": "PRD001",
    "location_id": "WH001",
    "location_type": "warehouse",
    "current_stock": 95,
    "available_stock": 95,
    "reserved_stock": 0,
    "initial_stock": 100,
    "transactions_count": 5,
    "total_sales": 5,
    "total_restock": 0,
    "last_updated": "2026-05-08T10:15:00Z",
    "quantity": 95
  }
]
```

### 5. Check the Frontend

Open browser to: http://localhost:5173

#### Warehouses Page
- Check that utilization is 50-70% (not 1000%+)
- Check that capacity is 100,000-300,000 (not 5,000-15,000)
- Check that location shows "Maharashtra, India" (not "undefined, undefined")

#### Stores Page
- Check that utilization is 50-70% (not 1000%+)
- Check that capacity is 10,000-30,000 (not 200-800)
- Check that location shows "Maharashtra, India" (not "undefined, undefined")

#### Inventory Page
- Check that Current Stock column shows live values
- Check that Available Stock column shows live values
- Check that Reserved Stock column shows live values
- Check that Transactions column shows transaction count
- Check that Total Sales column shows total sales volume

## Common Issues and Solutions

### Issue: "undefined, undefined" in location
**Cause**: Database has NaN values in location fields
**Fix**: Run `python scripts/fix_system.py` to re-seed with proper defaults

### Issue: Utilization shows 1000%+
**Cause**: Capacity values are too small (5K-15K) for actual stock (700K+)
**Fix**: Run `python scripts/fix_system.py` to increase capacities

### Issue: No live stock data showing
**Cause**: Frontend using old field names (`quantity` instead of `current_stock`)
**Fix**: Frontend files have already been fixed

### Issue: Old data still showing
**Cause**: Browser cache or database has old data
**Fix**: 
1. Clear browser cache (Ctrl+Shift+R)
2. Run `python scripts/fix_system.py` to clear and re-seed database

## Summary of All Fixes

### Backend Fixes (Already Done)
1. ✅ Increased warehouse capacity from 5K-15K to 100K-300K
2. ✅ Increased store capacity from 200-800 to 10K-30K
3. ✅ Added live tracking fields to inventory
4. ✅ Fixed NaN value handling in location data
5. ✅ Created transaction processing service
6. ✅ Created order simulator for initial data
7. ✅ Updated API response models

### Frontend Fixes (Just Done)
1. ✅ Fixed Warehouses.jsx: Changed `total_capacity` to `capacity`
2. ✅ Fixed Stores.jsx: Changed `total_capacity` to `capacity`
3. ✅ Fixed Inventory.jsx: Added live tracking fields
4. ✅ Fixed Inventory.jsx: Updated chart data calculation

### Next Steps
1. Run `backend/scripts/fix_system.py` to clear and re-seed database
2. Restart backend server
3. Clear browser cache
4. Refresh frontend pages
5. Verify all fixes are working correctly

## Quick Verification Commands

```bash
# Check database has correct capacities
cd backend
python -c "
from db.connection import mongodb
mongodb.connect()
db = mongodb.get_database()

print('=== WAREHOUSE CAPACITIES ===')
for wh in db.warehouses.find():
    pct = wh['current_utilization'] / wh['capacity'] * 100
    print(f\"{wh['warehouse_id']}: {pct:.1f}% ({wh['current_utilization']:,} / {wh['capacity']:,})\")
    
print('\\n=== STORE CAPACITIES ===')
for st in db.stores.find():
    pct = st['current_utilization'] / st['capacity'] * 100
    print(f\"{st['store_id']}: {pct:.1f}% ({st['current_utilization']:,} / {st['capacity']:,})\")

print('\\n=== LIVE TRACKING FIELDS ===')
inv = db.inventory.find_one()
print(f\"Current Stock: {inv.get('current_stock', 'NOT FOUND')}\")
print(f\"Available Stock: {inv.get('available_stock', 'NOT FOUND')}\")
print(f\"Reserved Stock: {inv.get('reserved_stock', 'NOT FOUND')}\")
print(f\"Transactions: {inv.get('transactions_count', 'NOT FOUND')}\")
print(f\"Total Sales: {inv.get('total_sales', 'NOT FOUND')}\")

mongodb.disconnect()
"
```

Expected output:
```
=== WAREHOUSE CAPACITIES ===
WH001: 63.3% (95,000 / 150,000)
WH002: 60.0% (120,000 / 200,000)
WH003: 60.0% (105,000 / 175,000)

=== STORE CAPACITIES ===
ST001: 50.0% (7,500 / 15,000)
ST002: 50.0% (10,000 / 20,000)
ST003: 50.0% (9,000 / 18,000)

=== LIVE TRACKING FIELDS ===
Current Stock: 95
Available Stock: 95
Reserved Stock: 0
Transactions: 5
Total Sales: 5
```

All frontend issues have been fixed! 🎉