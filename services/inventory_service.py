"""
Inventory Service - Inventory management with allocation support
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for inventory management with reservation support"""
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def get_inventory(self, sku: str = None, location_id: str = None, location_type: str = None) -> List[Dict[str, Any]]:
        """Get inventory with optional filters"""
        query = {}
        if sku:
            query["sku"] = sku
        if location_id:
            query["location_id"] = location_id
        if location_type:
            query["location_type"] = location_type
        
        return list(self.db.inventory.find(query, {"_id": 0}))
    
    def get_available_stock(self, sku: str, location_id: str) -> int:
        """
        Get available stock (total - reserved) for a product at a location.
        """
        inventory = self.db.inventory.find_one({
            "sku": sku,
            "location_id": location_id
        })
        
        if not inventory:
            return 0
        
        quantity = inventory.get("quantity", 0)
        reserved = inventory.get("reserved_stock", 0)
        return max(0, quantity - reserved)
    
    def check_stock_availability(self, sku: str, location_id: str, quantity: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if sufficient stock is available.
        
        Returns:
            Tuple of (is_available, details)
        """
        inventory = self.db.inventory.find_one({
            "sku": sku,
            "location_id": location_id
        })
        
        if not inventory:
            return False, {
                "error": "inventory_not_found",
                "message": f"No inventory record for SKU {sku} at {location_id}"
            }
        
        total = inventory.get("quantity", 0)
        reserved = inventory.get("reserved_stock", 0)
        available = total - reserved
        
        details = {
            "sku": sku,
            "location_id": location_id,
            "total_stock": total,
            "reserved_stock": reserved,
            "available_stock": available,
            "requested_quantity": quantity,
            "is_sufficient": available >= quantity
        }
        
        return available >= quantity, details
    
    def allocate_inventory(
        self, 
        warehouse_id: str, 
        sku: str, 
        quantity: int,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Allocate inventory by reserving stock.
        
        This reserves stock without reducing the total quantity.
        Stock is only reduced when the order ships.
        
        Args:
            warehouse_id: Warehouse ID
            sku: Product SKU
            quantity: Quantity to allocate
            order_id: Optional order ID for tracking
        
        Returns:
            Allocation result with before/after stock levels
        """
        try:
            # Find inventory record
            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id,
                "location_type": "warehouse"
            })
            
            if not inventory:
                raise ValueError(f"Inventory not found for SKU {sku} at warehouse {warehouse_id}")
            
            # Calculate available stock
            total = inventory.get("quantity", 0)
            current_reserved = inventory.get("reserved_stock", 0)
            available = total - current_reserved
            
            if available < quantity:
                raise ValueError(
                    f"Insufficient stock. Available: {available}, Requested: {quantity}"
                )
            
            # Record before state
            before_state = {
                "total_stock": total,
                "reserved_stock": current_reserved,
                "available_stock": available
            }
            
            # Update reserved stock
            new_reserved = current_reserved + quantity
            
            result = self.db.inventory.update_one(
                {"_id": inventory["_id"]},
                {
                    "$set": {
                        "reserved_stock": new_reserved,
                        "last_stock_check": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise ValueError("Failed to update inventory")
            
            # Record after state
            after_state = {
                "total_stock": total,
                "reserved_stock": new_reserved,
                "available_stock": total - new_reserved
            }
            
            allocation_result = {
                "success": True,
                "sku": sku,
                "warehouse_id": warehouse_id,
                "quantity_allocated": quantity,
                "order_id": order_id,
                "before": before_state,
                "after": after_state,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Allocated {quantity} units of {sku} at {warehouse_id} "
                f"(available: {before_state['available_stock']} -> {after_state['available_stock']})"
            )
            
            # Event trigger: Check inventory health after allocation
            self._trigger_inventory_check(sku, warehouse_id)
            
            return allocation_result
            
        except Exception as e:
            logger.error(f"Error allocating inventory: {e}")
            raise
    
    def release_allocation(
        self, 
        warehouse_id: str, 
        sku: str, 
        quantity: int
    ) -> Dict[str, Any]:
        """
        Release previously allocated (reserved) inventory.
        Used when an order is cancelled.
        """
        try:
            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id,
                "location_type": "warehouse"
            })
            
            if not inventory:
                raise ValueError(f"Inventory not found for SKU {sku} at warehouse {warehouse_id}")
            
            current_reserved = inventory.get("reserved_stock", 0)
            new_reserved = max(0, current_reserved - quantity)
            
            result = self.db.inventory.update_one(
                {"_id": inventory["_id"]},
                {
                    "$set": {
                        "reserved_stock": new_reserved,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Released {quantity} units of {sku} at {warehouse_id}")
            
            return {
                "success": True,
                "sku": sku,
                "warehouse_id": warehouse_id,
                "quantity_released": quantity,
                "reserved_before": current_reserved,
                "reserved_after": new_reserved
            }
            
        except Exception as e:
            logger.error(f"Error releasing allocation: {e}")
            raise
    
    def confirm_shipment(
        self, 
        warehouse_id: str, 
        sku: str, 
        quantity: int
    ) -> Dict[str, Any]:
        """
        Confirm shipment by reducing both total stock and reserved stock.
        Called when order actually ships.
        """
        try:
            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id,
                "location_type": "warehouse"
            })
            
            if not inventory:
                raise ValueError(f"Inventory not found for SKU {sku} at warehouse {warehouse_id}")
            
            current_quantity = inventory.get("quantity", 0)
            current_reserved = inventory.get("reserved_stock", 0)
            
            # Reduce both quantity and reserved
            new_quantity = max(0, current_quantity - quantity)
            new_reserved = max(0, current_reserved - quantity)
            
            result = self.db.inventory.update_one(
                {"_id": inventory["_id"]},
                {
                    "$set": {
                        "quantity": new_quantity,
                        "reserved_stock": new_reserved,
                        "last_stock_check": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(
                f"Confirmed shipment of {quantity} units of {sku} from {warehouse_id} "
                f"(stock: {current_quantity} -> {new_quantity})"
            )
            
            # Event trigger: Check inventory health after shipment
            self._trigger_inventory_check(sku, warehouse_id)
            
            return {
                "success": True,
                "sku": sku,
                "warehouse_id": warehouse_id,
                "quantity_shipped": quantity,
                "stock_before": current_quantity,
                "stock_after": new_quantity
            }
            
        except Exception as e:
            logger.error(f"Error confirming shipment: {e}")
            raise
    
    def update_inventory(self, sku: str, location_id: str, quantity_change: int) -> Dict[str, Any]:
        """Update inventory quantity"""
        inventory = self.db.inventory.find_one({
            "sku": sku,
            "location_id": location_id
        })
        
        if not inventory:
            raise ValueError(f"Inventory not found for SKU {sku} at location {location_id}")
        
        new_quantity = inventory["quantity"] + quantity_change
        
        if new_quantity < 0:
            raise ValueError(f"Insufficient stock. Current: {inventory['quantity']}, Requested change: {quantity_change}")
        
        result = self.db.inventory.update_one(
            {"_id": inventory["_id"]},
            {
                "$set": {
                    "quantity": new_quantity,
                    "last_stock_check": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise ValueError("Failed to update inventory")
        
        updated_inventory = self.db.inventory.find_one({"_id": inventory["_id"]}, {"_id": 0})
        
        # Event trigger: Check inventory health after update
        self._trigger_inventory_check(sku, location_id)
        
        return updated_inventory
    
    def _trigger_inventory_check(self, sku: str, location_id: str):
        """
        Trigger inventory health check after inventory changes.
        This is an event-driven hook for the Sensing & Intelligence Layer.
        """
        try:
            from services.sensing_service import sensing_service
            sensing_service.check_inventory_health(sku, location_id)
        except ImportError:
            logger.debug("Sensing service not available for event trigger")
        except Exception as e:
            logger.warning(f"Error in inventory health check trigger: {e}")
    
    def get_low_stock_items(self, threshold: int = None) -> List[Dict[str, Any]]:
        """Get items with low stock"""
        from api.config import settings
        if threshold is None:
            threshold = settings.low_stock_threshold
        
        low_stock = self.db.inventory.find(
            {"quantity": {"$lt": threshold}},
            {"_id": 0}
        )
        
        return list(low_stock)
    
    def restock_inventory(self, sku: str, location_id: str, quantity: int) -> Dict[str, Any]:
        """Restock inventory"""
        inventory = self.db.inventory.find_one({
            "sku": sku,
            "location_id": location_id
        })
        
        if not inventory:
            raise ValueError(f"Inventory not found for SKU {sku} at location {location_id}")
        
        result = self.db.inventory.update_one(
            {"_id": inventory["_id"]},
            {
                "$set": {
                    "quantity": inventory["quantity"] + quantity,
                    "last_restocked": datetime.utcnow(),
                    "last_stock_check": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        updated_inventory = self.db.inventory.find_one({"_id": inventory["_id"]}, {"_id": 0})
        
        # Event trigger: Check inventory health after restock
        self._trigger_inventory_check(sku, location_id)
        
        return updated_inventory
