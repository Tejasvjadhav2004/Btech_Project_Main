"""
Stores Router - Store API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List
from db.connection import get_db
from api.models.store import StoreResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("", response_model=List[StoreResponse])
async def get_stores():
    """Get all stores"""
    db = get_db()
    stores = list(db.stores.find({}))
    
    for store in stores:
        store["id"] = str(store["_id"])
        del store["_id"]
    
    return stores


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: str):
    """Get store by ID"""
    db = get_db()
    store = db.stores.find_one({"store_id": store_id})
    
    if not store:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    
    store["id"] = str(store["_id"])
    del store["_id"]
    
    return store


@router.get("/{store_id}/inventory")
async def get_store_inventory(store_id: str):
    """Get inventory for a specific store"""
    db = get_db()
    store = db.stores.find_one({"store_id": store_id})
    
    if not store:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    
    inventory = list(db.inventory.find({
        "location_id": store_id,
        "location_type": "store"
    }, {"_id": 0}))
    
    return {
        "store_id": store_id,
        "inventory": inventory,
        "total_items": len(inventory)
    }
