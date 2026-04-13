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
    
    for warehouse in warehouses:
        warehouse["id"] = str(warehouse["_id"])
        del warehouse["_id"]
    
    return warehouses


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(warehouse_id: str):
    """Get warehouse by ID"""
    db = get_db()
    warehouse = db.warehouses.find_one({"warehouse_id": warehouse_id})
    
    if not warehouse:
        raise HTTPException(status_code=404, detail=f"Warehouse {warehouse_id} not found")
    
    warehouse["id"] = str(warehouse["_id"])
    del warehouse["_id"]
    
    return warehouse


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
