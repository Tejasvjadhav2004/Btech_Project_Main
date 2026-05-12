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
    logger.info(f"Fetching inventory - sku: {sku}, location_type: {location_type}, limit: {limit}, skip: {skip}")
    
    try:
        db = get_db()
        if db is None:
            logger.error("Database connection is None - MongoDB connection failed")
            raise HTTPException(status_code=503, detail="Database connection failed. Please check MongoDB connection.")
        
        logger.info(f"Database connection obtained: {db is not None}")
        
        query = {}
        
        if sku:
            query["sku"] = sku
        if location_type:
            query["location_type"] = location_type
        
        logger.info(f"Executing query: {query}")
        inventory = list(
            db.inventory.find(query)
            .skip(skip)
            .limit(limit)
        )
        logger.info(f"Found {len(inventory)} inventory items")
        
        # Log sample inventory data for debugging
        if inventory:
            logger.info(f"Sample inventory data (first item): {dict(list(inventory[0].items())[:10])}")
        
        # Ensure all required fields are present with default values
        processed_inventory = []
        for idx, inv in enumerate(inventory):
            try:
                inv_dict = dict(inv)
                inv_dict["id"] = str(inv_dict["_id"])
                del inv_dict["_id"]
                
                # Log the raw data for first item
                if idx == 0:
                    logger.info(f"Processing first inventory item - Raw keys: {list(inv_dict.keys())}")
                    logger.info(f"Current stock value: {inv_dict.get('current_stock', 'NOT FOUND')}")
                    logger.info(f"Quantity value: {inv_dict.get('quantity', 'NOT FOUND')}")
                
                # Set defaults for missing fields
                inv_dict.setdefault("available_stock", inv_dict.get("current_stock", inv_dict.get("quantity", 0)) - inv_dict.get("reserved_stock", 0))
                inv_dict.setdefault("incoming_stock", inv_dict.get("incoming_stock", 0))
                inv_dict.setdefault("damaged_stock", inv_dict.get("damaged_stock", 0))
                inv_dict.setdefault("inventory_status", inv_dict.get("inventory_status"))
                inv_dict.setdefault("initial_stock", inv_dict.get("current_stock", inv_dict.get("quantity", 0)))
                inv_dict.setdefault("transactions_count", inv_dict.get("transactions_count", 0))
                inv_dict.setdefault("total_sales", inv_dict.get("total_sales", 0))
                inv_dict.setdefault("total_restock", inv_dict.get("total_restock", 0))
                
                # Ensure datetime fields have valid values
                from datetime import datetime
                current_time = datetime.utcnow()
                inv_dict.setdefault("last_updated", inv_dict.get("last_updated") or current_time)
                inv_dict.setdefault("historical_avg_sales", inv_dict.get("historical_avg_sales"))
                inv_dict.setdefault("reorder_threshold", inv_dict.get("reorder_threshold", 20))
                inv_dict.setdefault("reorder_quantity", inv_dict.get("reorder_quantity", 50))
                inv_dict.setdefault("optimal_stock", inv_dict.get("optimal_stock"))
                inv_dict.setdefault("demand_trend", inv_dict.get("demand_trend"))
                inv_dict.setdefault("lead_time_days", inv_dict.get("lead_time_days"))
                inv_dict.setdefault("quantity", inv_dict.get("current_stock", inv_dict.get("quantity", 0)))
                inv_dict.setdefault("last_restocked", inv_dict.get("last_restocked"))
                inv_dict.setdefault("last_stock_check", inv_dict.get("last_stock_check"))
                
                # Ensure datetime fields have valid values
                from datetime import datetime
                current_time = datetime.utcnow()
                inv_dict.setdefault("created_at", inv_dict.get("created_at") or inv_dict.get("updated_at") or current_time)
                inv_dict.setdefault("updated_at", inv_dict.get("updated_at") or current_time)
                
                inv_dict.setdefault("stock_velocity", inv_dict.get("stock_velocity"))
                
                # Validate with Pydantic model
                if idx == 0:
                    logger.info(f"Attempting Pydantic validation for first item...")
                    try:
                        validated = InventoryResponse(**inv_dict)
                        logger.info(f"✓ Pydantic validation successful for first item")
                    except Exception as validation_error:
                        logger.error(f"✗ Pydantic validation failed: {validation_error}")
                        logger.error(f"Problematic fields - current_stock: {inv_dict.get('current_stock')}, quantity: {inv_dict.get('quantity')}")
                        raise
                
                processed_inventory.append(inv_dict)
                
            except Exception as item_error:
                logger.error(f"Error processing inventory item {idx}: {item_error}")
                logger.error(f"Item data: {dict(list(inv.items())[:20])}")
                raise
        
        logger.info(f"Successfully processed {len(processed_inventory)} inventory items")
        return processed_inventory
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{sku}", response_model=List[InventoryResponse])
async def get_inventory_by_sku(sku: str):
    """Get inventory for a specific SKU across all locations"""
    db = get_db()
    inventory = list(db.inventory.find({"sku": sku}))
    
    for inv in inventory:
        inv["id"] = str(inv["_id"])
        del inv["_id"]
    
    return inventory
