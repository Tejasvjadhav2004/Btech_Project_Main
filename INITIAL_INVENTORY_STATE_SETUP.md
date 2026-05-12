# Initial Inventory State Setup Guide

## Overview

This document explains how to use the new `initial_inventory_state.csv` to initialize your supply chain orchestration system with predefined inventory data.

## What Changed

### Before (Old System)
- Used `enhanced_supply_chain_data.csv` for initial setup
- CSV contained historical data (past sales, past stock levels)
- System treated historical data as current state
- Required order simulation to create realistic system state

### After (New System)
- Uses `initial_inventory_state.csv` for initial setup
- CSV contains current inventory state (starting point)
- System starts with predefined stock levels
- Ready for orchestration operations immediately

## Files Modified

### Backend Files

1. **`backend/scripts/initial_state_loader.py`** (NEW)
   - Loads initial inventory state from CSV
   - Extracts products, warehouses, stores from CSV
   - Validates CSV data

2. **`backend/api/config.py`** (MODIFIED)
   - Changed from `supply_chain_data_path` to `initial_inventory_state_path`
   - Points to `data/raw/initial_inventory_state.csv`

3. **`backend/.env`** (MODIFIED)
   - Updated to use `INITIAL_INVENTORY_STATE_PATH`

4. **`backend/scripts/seed_data.py`** (MODIFIED)
   - Now uses `InitialStateLoader` instead of `DataLoader`
   - No longer requires order simulation
   - Loads initial state and makes system ready for operations

### Frontend Files

1. **`frontend/src/pages/Inventory.jsx`** (MODIFIED)
   - Added columns for `incoming_stock`, `damaged_stock`, `inventory_status`
   - Added `getInventoryStatusColor()` function for status badges
   - Displays new fields from CSV

## CSV Format

### Required Columns

```csv
sku,product_category,location_id,location_city,location_type,current_stock,available_stock,reserved_stock,incoming_stock,damaged_stock,warehouse_capacity,store_capacity,product_price,supplier_name,primary_warehouse_id,secondary_warehouse_id,reorder_threshold,reorder_quantity,inventory_status,last_restock_date
```

### Column Descriptions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `sku` | string | Product identifier | SKU0000 |
| `product_category` | string | Product category | haircare, fashion, skincare, cosmetics |
| `location_id` | string | Warehouse or store ID | WH001, ST001 |
| `location_city` | string | City name | Mumbai, Delhi |
| `location_type` | string | Type of location | warehouse, store |
| `current_stock` | integer | Current stock level | 123 |
| `available_stock` | integer | Available for sale | 123 |
| `reserved_stock` | integer | Reserved for orders | 0 |
| `incoming_stock` | integer | In transit | 47 |
| `damaged_stock` | integer | Damaged goods | 2 |
| `warehouse_capacity` | integer | Warehouse capacity | 150000 |
| `store_capacity` | integer | Store capacity | 15000 |
| `product_price` | float | Product price (INR) | 74.97 |
| `supplier_name` | string | Supplier name | Supplier 1 |
| `primary_warehouse_id` | string | Primary warehouse | WH001 |
| `secondary_warehouse_id` | string | Secondary warehouse | WH005 |
| `reorder_threshold` | integer | Trigger reorder | 31 |
| `reorder_quantity` | integer | Quantity to reorder | 62 |
| `inventory_status` | string | Status indicator | Healthy, Low Stock, Overstocked |
| `last_restock_date` | date | Last restock date | 2026-04-23 |

## How to Use

### Step 1: Prepare CSV File

Create or update `initial_inventory_state.csv` with your desired initial inventory state.

**Requirements**:
- Each product must have exactly 1 warehouse record
- Each product can have 2-4 store records
- Total records: 350-400 (100 products × 1 warehouse + 2-4 stores)

### Step 2: Run Seed Script

```bash
cd backend
python scripts/seed_data.py
```

This will:
1. Load CSV file
2. Validate data
3. Extract products, warehouses, stores
4. Insert into MongoDB
5. Make system ready for orchestration

### Step 3: Start Backend Server

```bash
cd backend
python -m uvicorn api.main:app --reload
```

### Step 4: Start Frontend

```bash
cd frontend
npm run dev
```

### Step 5: Access Application

Open browser at: `http://localhost:5173`

## What Happens After Initialization

### Initial State

After running `seed_data.py`, the system will have:

- **100 Products** with metadata (name, category, price)
- **5 Warehouses** with capacities (150K-170K units)
- **8 Stores** with capacities (15K-25K units)
- **350-400 Inventory Records** with predefined stock levels

### Ready for Orchestration

The system is now ready for:
- **Transaction Processing**: Sales, restocks, transfers
- **Alert Generation**: Low stock, overstock alerts
- **Demand Forecasting**: Predict future demand
- **Inventory Optimization**: Suggest optimal stock levels
- **Real-time Tracking**: Live inventory updates

## Example CSV Records

### Warehouse Record
```csv
SKU0000,haircare,WH001,Mumbai,warehouse,123,123,0,47,2,150000.0,,74.97,Supplier 1,WH001,WH005,31,62,Overstocked,2026-04-23
```

### Store Record
```csv
SKU0000,haircare,ST007,Pune,store,28,28,0,17,0,,18000.0,74.97,Supplier 1,WH001,WH005,7,14,Low Stock,2026-04-01
```

## System Configuration

### Backend Configuration

```python
# backend/api/config.py
initial_inventory_state_path: str = os.path.join("data", "raw", "initial_inventory_state.csv")
```

### Environment Variables

```bash
# backend/.env
INITIAL_INVENTORY_STATE_PATH=data/raw/initial_inventory_state.csv
```

## Validation

The system validates:
- ✅ All required columns present
- ✅ SKU values are unique
- ✅ Location IDs are valid
- ✅ Stock levels are non-negative
- ✅ Capacities are positive
- ✅ Prices are positive
- ✅ Dates are valid

## Troubleshooting

### CSV Not Found

**Error**: `FileNotFoundError: initial_inventory_state.csv`

**Solution**: Ensure CSV file exists at `backend/data/raw/initial_inventory_state.csv`

### Validation Failed

**Error**: `Missing columns: [column_name]`

**Solution**: Add missing columns to CSV file

### No Data Loaded

**Error**: `Loaded 0 initial inventory records`

**Solution**: Check CSV file has data and correct format

### Frontend Shows No Data

**Error**: Inventory page shows "No inventory records found"

**Solution**: 
1. Run `python scripts/seed_data.py`
2. Restart backend server
3. Refresh frontend page

## Benefits of New System

### ✅ Clear Separation

- **Historical Data**: For ML/analysis (separate CSV)
- **Initial State**: For orchestration demo (this CSV)

### ✅ Reproducible Demos

- Same CSV = Same starting point
- Easy to create different scenarios
- Consistent demos across environments

### ✅ Easy Customization

- Change stock levels in CSV
- Add/remove products easily
- Adjust warehouse/store capacities
- Perfect for different demo scenarios

### ✅ Ready for Orchestration

- No order simulation needed
- System ready immediately
- Can start processing transactions
- Perfect for demonstrating features

## Summary

The new `initial_inventory_state.csv` provides a clean starting point for your supply chain orchestration demo. The system loads this CSV, initializes MongoDB with predefined inventory state, and is immediately ready for orchestration operations.

**Key Points**:
- CSV contains current inventory state (not historical data)
- System starts with predefined stock levels
- Ready for orchestration operations immediately
- Easy to customize for different scenarios
- Perfect for demonstrating orchestration features

For questions or issues, refer to the troubleshooting section or check the logs in the backend console.
