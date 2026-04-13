"""
Warehouse Service - Warehouse selection and management
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db.connection import mongodb
import logging
import math

logger = logging.getLogger(__name__)


# Default coordinates for major Indian cities (fallback when coordinates not available)
CITY_COORDINATES = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462},
    "Surat": {"lat": 21.1702, "lon": 72.8311},
    "Kanpur": {"lat": 26.4499, "lon": 80.3319},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882},
    "Indore": {"lat": 22.7196, "lon": 75.8577},
    "Thane": {"lat": 19.2183, "lon": 72.9781},
    "Bhopal": {"lat": 23.2599, "lon": 77.4126},
    "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
    "Patna": {"lat": 25.5941, "lon": 85.1376},
    "Vadodara": {"lat": 22.3072, "lon": 73.1812},
    "Ghaziabad": {"lat": 28.6692, "lon": 77.4538},
    "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
    "Agra": {"lat": 27.1767, "lon": 78.0081},
    "Nashik": {"lat": 19.9975, "lon": 73.7898},
    "Faridabad": {"lat": 28.4089, "lon": 77.3178},
    "Meerut": {"lat": 28.9845, "lon": 77.7064},
    "Rajkot": {"lat": 22.3039, "lon": 70.8022},
    "Varanasi": {"lat": 25.3176, "lon": 82.9739},
    "Srinagar": {"lat": 34.0837, "lon": 74.7973},
    "Aurangabad": {"lat": 19.8762, "lon": 75.3433},
    "Dhanbad": {"lat": 23.7957, "lon": 86.4304},
    "Amritsar": {"lat": 31.6340, "lon": 74.8723},
    "Allahabad": {"lat": 25.4358, "lon": 81.8463},
    "Ranchi": {"lat": 23.3441, "lon": 85.3096},
    "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
    "Jabalpur": {"lat": 23.1815, "lon": 79.9864},
    "Gwalior": {"lat": 26.2183, "lon": 78.1828},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Jodhpur": {"lat": 26.2389, "lon": 73.0243},
    "Madurai": {"lat": 9.9252, "lon": 78.1198},
    "Raipur": {"lat": 21.2514, "lon": 81.6296},
    "Kochi": {"lat": 9.9312, "lon": 76.2673},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "Guwahati": {"lat": 26.1445, "lon": 91.7362},
    "Solapur": {"lat": 17.6599, "lon": 75.9064},
    "Hubli": {"lat": 15.3647, "lon": 75.1240},
    "Tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
    "Bareilly": {"lat": 28.3670, "lon": 79.4304},
    "Mysore": {"lat": 12.2958, "lon": 76.6394},
    "Gurgaon": {"lat": 28.4595, "lon": 77.0266},
    "Noida": {"lat": 28.5355, "lon": 77.3910},
}


class WarehouseService:
    """Service for warehouse selection and management"""
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def get_coordinates(self, location: Dict[str, Any]) -> Tuple[float, float]:
        """
        Get coordinates for a location.
        Uses stored coordinates if available, otherwise falls back to city mapping.
        """
        # Check if coordinates are stored
        if location.get("coordinates"):
            coords = location["coordinates"]
            if "lat" in coords and "lon" in coords:
                return coords["lat"], coords["lon"]
        
        # Fallback to city mapping
        city = location.get("city", "")
        if city in CITY_COORDINATES:
            coords = CITY_COORDINATES[city]
            return coords["lat"], coords["lon"]
        
        # Default to Mumbai if city not found
        logger.warning(f"Coordinates not found for city: {city}, using Mumbai as default")
        return CITY_COORDINATES["Mumbai"]["lat"], CITY_COORDINATES["Mumbai"]["lon"]
    
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
