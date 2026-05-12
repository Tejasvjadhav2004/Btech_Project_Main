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
    
    # Transform store data to match StoreResponse model
    response_stores = []
    for store in stores:
        # Get location from nested object or fall back to flat fields
        location_data = store.get("location", {})
        location = {
            "city": location_data.get("city", store.get("location_city", "Unknown")),
            "state": location_data.get("state", store.get("location_state")),
            "country": location_data.get("country", store.get("location_country", "India")),
            "coordinates": location_data.get("coordinates", store.get("coordinates"))
        }
        
        # Build response object matching StoreResponse schema
        response_store = {
            "id": str(store["_id"]),
            "store_id": store.get("store_id", ""),
            "name": store.get("name", ""),
            "location": location,
            "store_type": store.get("store_type", "Boutique"),
            "capacity": store.get("capacity", 10000),
            "current_utilization": store.get("current_utilization", 0),
            "is_active": store.get("is_active", True),
            "created_at": store.get("created_at"),
            "updated_at": store.get("updated_at"),
            "customer_metrics": store.get("customer_metrics")
        }
        
        response_stores.append(response_store)
    
    return response_stores


@router.get("/{store_id}", response_model=StoreResponse)
async def get_store(store_id: str):
    """Get store by ID"""
    db = get_db()
    store = db.stores.find_one({"store_id": store_id})
    
    if not store:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
    
    # Get location from nested object or fall back to flat fields
    location_data = store.get("location", {})
    location = {
        "city": location_data.get("city", store.get("location_city", "Unknown")),
        "state": location_data.get("state", store.get("location_state")),
        "country": location_data.get("country", store.get("location_country", "India")),
        "coordinates": location_data.get("coordinates", store.get("coordinates"))
    }
    
    # Build response object matching StoreResponse schema
    response_store = {
        "id": str(store["_id"]),
        "store_id": store.get("store_id", ""),
        "name": store.get("name", ""),
        "location": location,
        "store_type": store.get("store_type", "Boutique"),
        "capacity": store.get("capacity", 10000),
        "current_utilization": store.get("current_utilization", 0),
        "is_active": store.get("is_active", True),
        "created_at": store.get("created_at"),
        "updated_at": store.get("updated_at"),
        "customer_metrics": store.get("customer_metrics")
    }
    
    return response_store


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
