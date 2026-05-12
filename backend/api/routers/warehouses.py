"""
Warehouses Router - Warehouse API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from db.connection import get_db
from api.models.warehouse import WarehouseResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])


@router.get("", response_model=List[WarehouseResponse])
async def get_warehouses():
    """Get all warehouses"""
    db = get_db()
    warehouses = list(db.warehouses.find({}))
    
    # Transform warehouse data to match WarehouseResponse model
    response_warehouses = []
    for warehouse in warehouses:
        # Get location from nested object or fall back to flat fields
        location_data = warehouse.get("location", {})
        location = {
            "city": location_data.get("city", warehouse.get("location_city", "Unknown")),
            "state": location_data.get("state", warehouse.get("location_state")),
            "country": location_data.get("country", warehouse.get("location_country", "India")),
            "coordinates": location_data.get("coordinates", warehouse.get("coordinates"))
        }
        
        # Build response object matching WarehouseResponse schema
        response_warehouse = {
            "id": str(warehouse["_id"]),
            "warehouse_id": warehouse.get("warehouse_id", ""),
            "name": warehouse.get("name", ""),
            "location": location,
            "capacity": warehouse.get("capacity", 150000),
            "current_utilization": warehouse.get("current_utilization", 0),
            "is_active": warehouse.get("is_active", True),
            "created_at": warehouse.get("created_at"),
            "updated_at": warehouse.get("updated_at"),
            "efficiency_metrics": warehouse.get("efficiency_metrics")
        }
        
        response_warehouses.append(response_warehouse)
    
    return response_warehouses


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str):
    """Get warehouse by ID"""
    db = get_db()
    warehouse = db.warehouses.find_one({"warehouse_id": warehouse_id})
    
    if not warehouse:
        raise HTTPException(status_code=404, detail=f"Warehouse {warehouse_id} not found")
    
    # Get location from nested object or fall back to flat fields
    location_data = warehouse.get("location", {})
    location = {
        "city": location_data.get("city", warehouse.get("location_city", "Unknown")),
        "state": location_data.get("state", warehouse.get("location_state")),
        "country": location_data.get("country", warehouse.get("location_country", "India")),
        "coordinates": location_data.get("coordinates", warehouse.get("coordinates"))
    }
    
    # Build response object matching WarehouseResponse schema
    response_warehouse = {
        "id": str(warehouse["_id"]),
        "warehouse_id": warehouse.get("warehouse_id", ""),
        "name": warehouse.get("name", ""),
        "location": location,
        "capacity": warehouse.get("capacity", 150000),
        "current_utilization": warehouse.get("current_utilization", 0),
        "is_active": warehouse.get("is_active", True),
        "created_at": warehouse.get("created_at"),
        "updated_at": warehouse.get("updated_at"),
        "efficiency_metrics": warehouse.get("efficiency_metrics")
    }
    
    return response_warehouse


@router.get("/{warehouse_id}/inventory")
async def get_warehouse_inventory(warehouse_id: str):
    """Get inventory for a specific warehouse"""
    db = get_db()
    warehouse = db.warehouses.find_one({"warehouse_id": warehouse_id})
    
    if not warehouse:
        raise HTTPException(status_code=404, detail=f"Warehouse {warehouse_id} not found")
    
    inventory = list(db.inventory.find({
        "location_id": warehouse_id,
        "location_type": "warehouse"
    }, {"_id": 0}))
    
    return {
        "warehouse_id": warehouse_id,
        "inventory": inventory,
        "total_items": len(inventory)
    }


@router.get("/by-city/{city}")
async def get_warehouses_by_city(city: str):
    """Get warehouses in a specific city"""
    db = get_db()
    warehouses = list(db.warehouses.find(
        {"location.city": city},
        {"_id": 0}
    ))
    return {"warehouses": warehouses}
