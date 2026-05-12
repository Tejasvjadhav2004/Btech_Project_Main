"""
Warehouse Service - Warehouse selection and management
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db.connection import mongodb
import logging
import math

logger = logging.getLogger(__name__)


class WarehouseService:
    """Service for warehouse selection and management"""
    
    def __init__(self):
        # Don't cache database reference - get it dynamically each time
        pass
    
    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()
    
    def get_coordinates(self, location: Dict[str, Any]) -> Tuple[float, float]:
        """
        Get coordinates for a location.
        Uses stored coordinates from database, falls back to city mapping if needed.
        """
        # Check if coordinates are stored in location object
        if location.get("coordinates"):
            coords = location["coordinates"]
            if "lat" in coords and "lon" in coords:
                return coords["lat"], coords["lon"]

        # Get coordinates from database for city
        city = location.get("city", "")
        if city:
            # Query database for city coordinates
            location_doc = self.db.locations.find_one({"city": city})
            if location_doc:
                return location_doc["lat"], location_doc["lng"]

        # Default to Mumbai if city not found
        logger.warning(f"Coordinates not found for city: {city}, using Mumbai as default")
        return 19.0760, 72.8777
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_warehouse_utilization(self, warehouse: Dict[str, Any]) -> float:
        """Calculate warehouse utilization percentage"""
        capacity = warehouse.get("capacity", 1)
        current = warehouse.get("current_utilization", 0)
        if capacity == 0:
            return 100.0
        return (current / capacity) * 100
    
    def get_warehouse_stock(self, warehouse_id: str, sku: str) -> int:
        """Get available stock for a product in a warehouse"""
        inventory = self.db.inventory.find_one({
            "location_id": warehouse_id,
            "location_type": "warehouse",
            "sku": sku
        })
        
        if not inventory:
            return 0
        
        # Available = total quantity - reserved
        quantity = inventory.get("quantity", 0)
        reserved = inventory.get("reserved_stock", 0)
        return max(0, quantity - reserved)
    
    def select_warehouse(
        self, 
        sku: str, 
        store_id: str, 
        quantity: int = 1,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Select the best warehouse for fulfilling an order.
        
        Decision factors (in order of priority):
        1. Stock availability (must have enough stock)
        2. Distance to store (prefer nearest)
        3. Warehouse utilization (prefer less utilized as tiebreaker)
        
        Args:
            sku: Product SKU
            store_id: Destination store ID
            quantity: Required quantity
            priority: Order priority (normal/high)
        
        Returns:
            Dictionary with selected warehouse and decision details
        """
        try:
            # Get store location
            store = self.db.stores.find_one({"store_id": store_id})
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            store_coords = self.get_coordinates(store.get("location", {}))
            
            # Get all active warehouses
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            if not warehouses:
                raise ValueError("No active warehouses found")
            
            # Evaluate each warehouse
            candidates = []
            for warehouse in warehouses:
                warehouse_id = warehouse["warehouse_id"]
                
                # Check stock availability
                available_stock = self.get_warehouse_stock(warehouse_id, sku)
                if available_stock < quantity:
                    continue
                
                # Calculate distance
                wh_coords = self.get_coordinates(warehouse.get("location", {}))
                distance = self.calculate_distance(
                    store_coords[0], store_coords[1],
                    wh_coords[0], wh_coords[1]
                )
                
                # Get utilization
                utilization = self.get_warehouse_utilization(warehouse)
                
                candidates.append({
                    "warehouse_id": warehouse_id,
                    "warehouse_name": warehouse.get("name", warehouse_id),
                    "available_stock": available_stock,
                    "distance_km": round(distance, 2),
                    "utilization_percent": round(utilization, 2),
                    "city": warehouse.get("location", {}).get("city", "Unknown"),
                    "coordinates": {"lat": wh_coords[0], "lon": wh_coords[1]}
                })
            
            if not candidates:
                raise ValueError(f"No warehouse has sufficient stock for SKU {sku} (required: {quantity})")
            
            # Sort candidates:
            # Primary: distance (ascending)
            # Secondary: utilization (ascending - prefer less utilized)
            candidates.sort(key=lambda x: (x["distance_km"], x["utilization_percent"]))
            
            selected = candidates[0]
            
            # Build decision log
            decision = {
                "selected_warehouse": selected,
                "alternatives": candidates[1:5],  # Top 5 alternatives
                "decision_factors": {
                    "primary": "distance",
                    "secondary": "utilization",
                    "stock_filter": f">= {quantity} units"
                },
                "store": {
                    "store_id": store_id,
                    "city": store.get("location", {}).get("city", "Unknown"),
                    "coordinates": {"lat": store_coords[0], "lon": store_coords[1]}
                },
                "sku": sku,
                "required_quantity": quantity,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Selected warehouse {selected['warehouse_id']} for SKU {sku} "
                f"(distance: {selected['distance_km']}km, stock: {selected['available_stock']})"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error selecting warehouse: {e}")
            raise
    
    def get_warehouses_with_stock(self, sku: str, min_quantity: int = 1) -> List[Dict[str, Any]]:
        """Get all warehouses that have stock for a product"""
        warehouses = list(self.db.warehouses.find({"is_active": True}))
        result = []
        
        for warehouse in warehouses:
            available = self.get_warehouse_stock(warehouse["warehouse_id"], sku)
            if available >= min_quantity:
                result.append({
                    "warehouse_id": warehouse["warehouse_id"],
                    "name": warehouse.get("name"),
                    "city": warehouse.get("location", {}).get("city"),
                    "available_stock": available,
                    "utilization": self.get_warehouse_utilization(warehouse)
                })
        
        return result
    
    def get_warehouse_distance_to_store(self, warehouse_id: str, store_id: str) -> float:
        """Calculate distance between a warehouse and store"""
        warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
        store = self.db.stores.find_one({"store_id": store_id})
        
        if not warehouse or not store:
            raise ValueError("Warehouse or store not found")
        
        wh_coords = self.get_coordinates(warehouse.get("location", {}))
        store_coords = self.get_coordinates(store.get("location", {}))
        
        return self.calculate_distance(
            wh_coords[0], wh_coords[1],
            store_coords[0], store_coords[1]
        )
    
    def get_all_warehouses(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all warehouses with utilization info"""
        query = {"is_active": True} if active_only else {}
        warehouses = list(self.db.warehouses.find(query))
        
        for warehouse in warehouses:
            warehouse["utilization_percent"] = self.get_warehouse_utilization(warehouse)
            warehouse["id"] = str(warehouse.pop("_id"))
        
        return warehouses
