"""
Delivery Service - Delivery creation and simulation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
from services.warehouse_service import WarehouseService
import logging
import uuid

logger = logging.getLogger(__name__)


class DeliveryService:
    """Service for delivery management and simulation"""
    
    # Speed constants (km/h)
    TRANSPORT_SPEEDS = {
        "truck": 50,      # Average truck speed including stops
        "air": 500,       # Air freight average
        "rail": 80,       # Rail freight average
        "express": 100    # Express delivery (priority trucks)
    }
    
    # Distance thresholds for transport mode selection
    DISTANCE_THRESHOLDS = {
        "local": 100,      # < 100km: local delivery
        "regional": 500,   # 100-500km: regional
        "national": 1500,  # 500-1500km: national
        "long_haul": 2000  # > 1500km: long haul
    }
    
    def __init__(self):
        self.db = mongodb.get_database()
        self.warehouse_service = WarehouseService()
    
    def _generate_delivery_id(self) -> str:
        """Generate unique delivery ID"""
        return f"DEL-{uuid.uuid4().hex[:8].upper()}"
    
    def _select_transport_mode(
        self, 
        distance_km: float, 
        priority: str = "normal"
    ) -> str:
        """
        Select transport mode based on distance and priority.
        
        Rules:
        - High priority + long distance: air
        - High priority + short distance: express
        - Normal priority: truck (default)
        - Very long distance: consider air even for normal priority
        """
        if priority == "high":
            if distance_km > self.DISTANCE_THRESHOLDS["regional"]:
                return "air"
            return "express"
        
        # For normal priority
        if distance_km > self.DISTANCE_THRESHOLDS["long_haul"]:
            return "air"  # Air is more efficient for very long distances
        
        return "truck"
    
    def _estimate_delivery_time(
        self, 
        distance_km: float, 
        transport_mode: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Estimate delivery time based on distance and transport mode.
        
        Returns dict with:
        - estimated_hours: Travel time in hours
        - buffer_hours: Additional buffer for loading/unloading
        - total_hours: Total estimated time
        - estimated_arrival: Estimated arrival datetime
        """
        speed = self.TRANSPORT_SPEEDS.get(transport_mode, 50)
        travel_hours = distance_km / speed
        
        # Add buffer time for loading, unloading, customs, etc.
        if transport_mode == "air":
            buffer_hours = 12  # Airport handling, customs
        elif transport_mode == "express":
            buffer_hours = 2   # Minimal buffer for express
        else:
            buffer_hours = 6   # Standard buffer for truck/rail
        
        # Priority orders get reduced buffer
        if priority == "high":
            buffer_hours = buffer_hours * 0.5
        
        total_hours = travel_hours + buffer_hours
        
        # Round up to nearest hour
        total_hours = round(total_hours, 1)
        
        estimated_arrival = datetime.utcnow() + timedelta(hours=total_hours)
        
        return {
            "travel_hours": round(travel_hours, 1),
            "buffer_hours": round(buffer_hours, 1),
            "total_hours": total_hours,
            "estimated_departure": datetime.utcnow() + timedelta(hours=1),  # 1 hour to prepare
            "estimated_arrival": estimated_arrival
        }
    
    def _build_route(
        self, 
        warehouse: Dict[str, Any], 
        store: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build route points for delivery"""
        route = [
            {
                "location_id": warehouse["warehouse_id"],
                "location_type": "warehouse",
                "city": warehouse.get("location", {}).get("city", "Unknown"),
                "coordinates": warehouse.get("location", {}).get("coordinates"),
                "sequence": 1,
                "action": "pickup"
            },
            {
                "location_id": store["store_id"],
                "location_type": "store",
                "city": store.get("location", {}).get("city", "Unknown"),
                "coordinates": store.get("location", {}).get("coordinates"),
                "sequence": 2,
                "action": "delivery"
            }
        ]
        return route
    
    def create_delivery(
        self,
        order_id: str,
        warehouse_id: str,
        store_id: str,
        priority: str = "normal",
        carrier: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a delivery for an order.
        
        This:
        1. Fetches warehouse and store details
        2. Calculates distance
        3. Selects transport mode
        4. Estimates delivery time
        5. Creates delivery record
        
        Args:
            order_id: Order ID being fulfilled
            warehouse_id: Source warehouse ID
            store_id: Destination store ID
            priority: Order priority (normal/high)
            carrier: Optional carrier name
            notes: Optional delivery notes
        
        Returns:
            Created delivery record
        """
        try:
            # Fetch warehouse details
            warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
            if not warehouse:
                raise ValueError(f"Warehouse {warehouse_id} not found")
            
            # Fetch store details
            store = self.db.stores.find_one({"store_id": store_id})
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            # Calculate distance
            distance_km = self.warehouse_service.get_warehouse_distance_to_store(
                warehouse_id, store_id
            )
            
            # Select transport mode
            transport_mode = self._select_transport_mode(distance_km, priority)
            
            # Estimate delivery time
            time_estimate = self._estimate_delivery_time(
                distance_km, transport_mode, priority
            )
            
            # Build route
            route = self._build_route(warehouse, store)
            
            # Generate delivery ID
            delivery_id = self._generate_delivery_id()
            
            # Create delivery document
            delivery = {
                "delivery_id": delivery_id,
                "order_id": order_id,
                "warehouse_id": warehouse_id,
                "store_id": store_id,
                "status": "pending",
                "transport_mode": transport_mode,
                "route": route,
                "distance_km": round(distance_km, 2),
                "estimated_departure": time_estimate["estimated_departure"],
                "actual_departure": None,
                "estimated_arrival": time_estimate["estimated_arrival"],
                "actual_arrival": None,
                "estimated_duration_hours": time_estimate["total_hours"],
                "carrier": carrier or f"SCM-Logistics-{transport_mode.upper()}",
                "tracking_number": f"TRK-{uuid.uuid4().hex[:10].upper()}",
                "notes": notes,
                "priority": priority,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Insert into database
            result = self.db.deliveries.insert_one(delivery)
            delivery["_id"] = result.inserted_id
            
            logger.info(
                f"Created delivery {delivery_id} for order {order_id}: "
                f"{warehouse_id} -> {store_id} ({distance_km:.1f}km, {transport_mode})"
            )
            
            return delivery
            
        except Exception as e:
            logger.error(f"Error creating delivery: {e}")
            raise
    
    def get_delivery(self, delivery_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery by ID"""
        delivery = self.db.deliveries.find_one({"delivery_id": delivery_id})
        if delivery:
            delivery["id"] = str(delivery.pop("_id"))
        return delivery
    
    def get_delivery_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get delivery for an order"""
        delivery = self.db.deliveries.find_one({"order_id": order_id})
        if delivery:
            delivery["id"] = str(delivery.pop("_id"))
        return delivery
    
    def get_deliveries(
        self, 
        status: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        store_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get deliveries with optional filters"""
        query = {}
        if status:
            query["status"] = status
        if warehouse_id:
            query["warehouse_id"] = warehouse_id
        if store_id:
            query["store_id"] = store_id
        
        deliveries = list(self.db.deliveries.find(query).sort(
            "created_at", -1
        ).limit(limit))
        
        for delivery in deliveries:
            delivery["id"] = str(delivery.pop("_id"))
        
        return deliveries
    
    def update_delivery_status(
        self, 
        delivery_id: str, 
        status: str,
        actual_departure: Optional[datetime] = None,
        actual_arrival: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update delivery status.
        
        Valid statuses: pending, in_transit, delivered, failed, cancelled
        """
        valid_statuses = ["pending", "in_transit", "delivered", "failed", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == "in_transit" and actual_departure is None:
            update_data["actual_departure"] = datetime.utcnow()
        elif actual_departure:
            update_data["actual_departure"] = actual_departure
        
        if status == "delivered":
            update_data["actual_arrival"] = actual_arrival or datetime.utcnow()
        elif actual_arrival:
            update_data["actual_arrival"] = actual_arrival
        
        result = self.db.deliveries.update_one(
            {"delivery_id": delivery_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Delivery {delivery_id} not found")
        
        logger.info(f"Updated delivery {delivery_id} status to {status}")
        
        # Event trigger: Check for delivery delays after status update
        if status == "in_transit":
            self._trigger_delivery_delay_check(delivery_id)
        
        return self.get_delivery(delivery_id)
    
    def start_delivery(self, delivery_id: str) -> Dict[str, Any]:
        """Start a delivery (mark as in_transit)"""
        return self.update_delivery_status(delivery_id, "in_transit")
    
    def complete_delivery(self, delivery_id: str) -> Dict[str, Any]:
        """Complete a delivery (mark as delivered)"""
        return self.update_delivery_status(delivery_id, "delivered")
    
    def cancel_delivery(self, delivery_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel a delivery"""
        delivery = self.update_delivery_status(delivery_id, "cancelled")
        
        if reason:
            self.db.deliveries.update_one(
                {"delivery_id": delivery_id},
                {"$set": {"cancellation_reason": reason}}
            )
        
        return self.get_delivery(delivery_id)
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_distance": {"$avg": "$distance_km"},
                    "avg_duration": {"$avg": "$estimated_duration_hours"}
                }
            }
        ]
        
        status_stats = list(self.db.deliveries.aggregate(pipeline))
        
        # Transport mode stats
        mode_pipeline = [
            {
                "$group": {
                    "_id": "$transport_mode",
                    "count": {"$sum": 1}
                }
            }
        ]
        mode_stats = list(self.db.deliveries.aggregate(mode_pipeline))
        
        return {
            "by_status": {item["_id"]: item for item in status_stats},
            "by_transport_mode": {item["_id"]: item["count"] for item in mode_stats},
            "total_deliveries": sum(item["count"] for item in status_stats)
        }
    
    def _trigger_delivery_delay_check(self, delivery_id: str):
        """
        Trigger delivery delay check for a specific delivery.
        This is an event-driven hook for the Sensing & Intelligence Layer.
        """
        try:
            from services.sensing_service import sensing_service
            # Check this specific delivery for potential delays
            sensing_service.detect_delivery_delay(source="event_trigger")
        except ImportError:
            logger.debug("Sensing service not available for event trigger")
        except Exception as e:
            logger.warning(f"Error in delivery delay check trigger: {e}")
