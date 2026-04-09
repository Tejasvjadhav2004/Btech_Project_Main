"""
Inventory Router - Inventory API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from db.connection import get_db
from api.models.inventory import InventoryResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=List[InventoryResponse])
async def get_inventory(
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    location_type: Optional[str] = Query(None, description="Filter by location type: warehouse or store"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get all inventory with optional filters"""
    db = get_db()
    query = {}
    
    if sku:
        query["sku"] = sku
    if location_type:
        query["location_type"] = location_type
    
    inventory = list(
        db.inventory.find(query)
        .skip(skip)
        .limit(limit)
    )
    
    for inv in inventory:
        inv["id"] = str(inv["_id"])
        del inv["_id"]
    
    return inventory


@router.get("/{sku}", response_model=List[InventoryResponse])
async def get_inventory_by_sku(sku: str):
    """Get inventory for a specific SKU across all locations"""
    db = get_db()
    inventory = list(db.inventory.find({"sku": sku}))
    
    for inv in inventory:
        inv["id"] = str(inv["_id"])
        del inv["_id"]
    
    return inventory
