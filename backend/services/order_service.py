"""
Order Service - Order processing and execution pipeline
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
from services.warehouse_service import WarehouseService
from services.inventory_service import InventoryService
from services.delivery_service import DeliveryService
from services.execution_logger import ExecutionLogger, ExecutionStep, ExecutionLogLevel
import logging
import uuid

logger = logging.getLogger(__name__)


class OrderPriority:
    """Order priority constants"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class OrderStatus:
    """Order status constants"""
    PENDING = "pending"
    ALLOCATED = "allocated"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderService:
    """Service for order processing and execution pipeline"""
    
    # Quantity thresholds for priority assignment
    HIGH_PRIORITY_QUANTITY = 100
    
    def __init__(self):
        self.db = mongodb.get_database()
        self.warehouse_service = WarehouseService()
        self.inventory_service = InventoryService()
        self.delivery_service = DeliveryService()
        self.execution_logger = ExecutionLogger()
    
    def _assign_priority(self, quantity: int, explicit_priority: Optional[str] = None) -> str:
        """
        Assign order priority based on quantity or explicit setting.
        
        Rules:
        - Explicit priority takes precedence
        - Quantity >= 100: high priority
        - Otherwise: normal priority
        """
        if explicit_priority and explicit_priority in [OrderPriority.HIGH, OrderPriority.NORMAL, OrderPriority.LOW]:
            return explicit_priority
        
        if quantity >= self.HIGH_PRIORITY_QUANTITY:
            return OrderPriority.HIGH
        
        return OrderPriority.NORMAL
    
    def _validate_order_input(self, sku: str, quantity: int, store_id: str) -> Dict[str, Any]:
        """
        Validate order input parameters.
        
        Checks:
        - Product exists
        - Store exists
        - Quantity is positive
        
        Returns validation result with details.
        """
        errors = []
        details = {}
        
        # Validate quantity
        if quantity <= 0:
            errors.append("Quantity must be positive")
        
        # Validate product
        product = self.db.products.find_one({"sku": sku})
        if not product:
            errors.append(f"Product with SKU {sku} not found")
        else:
            details["product"] = {
                "sku": sku,
                "name": product.get("name"),
                "price": product.get("price", 0)
            }
        
        # Validate store
        store = self.db.stores.find_one({"store_id": store_id})
        if not store:
            errors.append(f"Store {store_id} not found")
        else:
            details["store"] = {
                "store_id": store_id,
                "name": store.get("name"),
                "city": store.get("location", {}).get("city")
            }
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "details": details
        }
    
    def create_order(
        self,
        sku: str,
        quantity: int,
        store_id: str,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new order (simplified API).
        
        This creates an order with status 'pending'.
        The order must be processed separately using process_order().
        
        Args:
            sku: Product SKU
            quantity: Quantity to order
            store_id: Destination store ID
            priority: Optional priority (high/normal/low)
        
        Returns:
            Created order record
        """
        try:
            # Validate input
            validation = self._validate_order_input(sku, quantity, store_id)
            if not validation["valid"]:
                raise ValueError(f"Validation failed: {', '.join(validation['errors'])}")
            
            product = validation["details"]["product"]
            store = validation["details"]["store"]
            
            # Generate order ID
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            # Assign priority
            assigned_priority = self._assign_priority(quantity, priority)
            
            # Calculate total
            unit_price = product.get("price", 0)
            total_amount = unit_price * quantity
            
            # Get store details for shipping address
            store_doc = self.db.stores.find_one({"store_id": store_id})
            
            # Create order document
            order = {
                "order_id": order_id,
                "store_id": store_id,
                "items": [{
                    "sku": sku,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_price": total_amount
                }],
                "total_amount": total_amount,
                "status": OrderStatus.PENDING,
                "priority": assigned_priority,
                "order_date": datetime.utcnow(),
                "expected_delivery": None,
                "actual_delivery": None,
                "shipping_address": {
                    "city": store_doc.get("location", {}).get("city", "Unknown"),
                    "state": store_doc.get("location", {}).get("state"),
                    "country": store_doc.get("location", {}).get("country", "India")
                },
                "assigned_warehouse": None,
                "delivery_id": None,
                "allocation_details": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "fulfillment_priority": assigned_priority,
                "predicted_delay_risk": None,
                "optimal_route": None
            }
            
            # Insert order
            result = self.db.orders.insert_one(order)
            order["_id"] = result.inserted_id
            
            logger.info(f"Created order {order_id}: {quantity}x {sku} for store {store_id} (priority: {assigned_priority})")
            
            # Event trigger: Check for demand patterns after order creation
            self._trigger_demand_check()
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    def process_order(self, order_id: str) -> Dict[str, Any]:
        """
        Process an order through the complete execution pipeline.
        
        Pipeline steps:
        1. Fetch and validate order
        2. Select best warehouse
        3. Allocate inventory (reserve stock)
        4. Create delivery
        5. Update order status to 'allocated'
        
        Returns:
            Execution result with all details
        """
        # Create execution tracking
        execution_id = self.execution_logger.create_execution(order_id)
        
        try:
            # Step 1: Fetch order
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.ORDER_VALIDATED,
                f"Fetching order {order_id}",
                {"order_id": order_id}
            )
            
            order = self.get_order(order_id)
            
            if order["status"] != OrderStatus.PENDING:
                raise ValueError(f"Order {order_id} is not in pending status (current: {order['status']})")
            
            # Get order details
            item = order["items"][0]  # For simplified API, single item
            sku = item["sku"]
            quantity = item["quantity"]
            store_id = order["store_id"]
            priority = order.get("priority", OrderPriority.NORMAL)
            
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.ORDER_VALIDATED,
                f"Order validated: {quantity}x {sku} for store {store_id}",
                {
                    "sku": sku,
                    "quantity": quantity,
                    "store_id": store_id,
                    "priority": priority
                },
                ExecutionLogLevel.SUCCESS
            )
            
            # Step 2: Select warehouse
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.WAREHOUSE_SELECTED,
                "Selecting optimal warehouse...",
                {"sku": sku, "store_id": store_id, "quantity": quantity}
            )
            
            warehouse_decision = self.warehouse_service.select_warehouse(
                sku=sku,
                store_id=store_id,
                quantity=quantity,
                priority=priority
            )
            
            selected_warehouse = warehouse_decision["selected_warehouse"]
            warehouse_id = selected_warehouse["warehouse_id"]
            
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.WAREHOUSE_SELECTED,
                f"Selected warehouse: {warehouse_id} ({selected_warehouse['city']}, {selected_warehouse['distance_km']}km)",
                warehouse_decision,
                ExecutionLogLevel.SUCCESS
            )
            
            # Step 3: Allocate inventory
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.INVENTORY_ALLOCATED,
                f"Allocating {quantity} units from {warehouse_id}...",
                {"warehouse_id": warehouse_id, "sku": sku, "quantity": quantity}
            )
            
            allocation_result = self.inventory_service.allocate_inventory(
                warehouse_id=warehouse_id,
                sku=sku,
                quantity=quantity,
                order_id=order_id
            )
            
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.INVENTORY_ALLOCATED,
                f"Inventory allocated: {allocation_result['before']['available_stock']} -> {allocation_result['after']['available_stock']} available",
                allocation_result,
                ExecutionLogLevel.SUCCESS
            )
            
            # Step 4: Create delivery
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.DELIVERY_CREATED,
                f"Creating delivery from {warehouse_id} to {store_id}...",
                {"warehouse_id": warehouse_id, "store_id": store_id}
            )
            
            delivery = self.delivery_service.create_delivery(
                order_id=order_id,
                warehouse_id=warehouse_id,
                store_id=store_id,
                priority=priority
            )
            
            delivery_id = delivery["delivery_id"]
            
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.DELIVERY_CREATED,
                f"Delivery created: {delivery_id} ({delivery['transport_mode']}, {delivery['distance_km']}km, ETA: {delivery['estimated_duration_hours']}h)",
                {
                    "delivery_id": delivery_id,
                    "transport_mode": delivery["transport_mode"],
                    "distance_km": delivery["distance_km"],
                    "estimated_hours": delivery["estimated_duration_hours"]
                },
                ExecutionLogLevel.SUCCESS
            )
            
            # Step 5: Update order status
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.ORDER_STATUS_UPDATED,
                f"Updating order status to 'allocated'...",
                {"order_id": order_id}
            )
            
            # Update order with warehouse and delivery info
            self.db.orders.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": OrderStatus.ALLOCATED,
                        "assigned_warehouse": warehouse_id,
                        "delivery_id": delivery_id,
                        "allocation_details": {
                            "warehouse_decision": warehouse_decision,
                            "inventory_allocation": allocation_result
                        },
                        "expected_delivery": delivery["estimated_arrival"],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            self.execution_logger.log_step(
                execution_id,
                ExecutionStep.ORDER_STATUS_UPDATED,
                f"Order {order_id} status updated to 'allocated'",
                {"new_status": OrderStatus.ALLOCATED},
                ExecutionLogLevel.SUCCESS
            )
            
            # Complete execution
            execution_summary = {
                "order_id": order_id,
                "warehouse_id": warehouse_id,
                "delivery_id": delivery_id,
                "distance_km": selected_warehouse["distance_km"],
                "transport_mode": delivery["transport_mode"],
                "estimated_delivery": delivery["estimated_arrival"].isoformat() if delivery["estimated_arrival"] else None,
                "inventory_before": allocation_result["before"],
                "inventory_after": allocation_result["after"]
            }
            
            self.execution_logger.complete_execution(execution_id, "completed", execution_summary)
            
            # Fetch updated order
            updated_order = self.get_order(order_id)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "order": updated_order,
                "warehouse_decision": warehouse_decision,
                "allocation": allocation_result,
                "delivery": delivery,
                "summary": execution_summary
            }
            
        except Exception as e:
            # Log failure
            self.execution_logger.fail_execution(
                execution_id,
                str(e),
                {"order_id": order_id, "error_type": type(e).__name__}
            )
            logger.error(f"Order processing failed for {order_id}: {e}")
            raise
    
    def ship_order(self, order_id: str) -> Dict[str, Any]:
        """
        Ship an order (transition from allocated to shipped).
        
        This:
        1. Confirms inventory shipment (reduces actual stock)
        2. Updates delivery status to in_transit
        3. Updates order status to shipped
        """
        order = self.get_order(order_id)
        
        if order["status"] != OrderStatus.ALLOCATED:
            raise ValueError(f"Order {order_id} must be in 'allocated' status to ship (current: {order['status']})")
        
        # Get details
        item = order["items"][0]
        sku = item["sku"]
        quantity = item["quantity"]
        warehouse_id = order["assigned_warehouse"]
        delivery_id = order["delivery_id"]
        
        # Confirm shipment (reduces actual stock)
        self.inventory_service.confirm_shipment(warehouse_id, sku, quantity)
        
        # Update delivery status
        self.delivery_service.start_delivery(delivery_id)
        
        # Update order status
        self.db.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": OrderStatus.SHIPPED,
                    "shipped_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Order {order_id} shipped")
        return self.get_order(order_id)
    
    def deliver_order(self, order_id: str) -> Dict[str, Any]:
        """
        Mark order as delivered.
        """
        order = self.get_order(order_id)
        
        if order["status"] != OrderStatus.SHIPPED:
            raise ValueError(f"Order {order_id} must be in 'shipped' status to deliver (current: {order['status']})")
        
        delivery_id = order["delivery_id"]
        
        # Complete delivery
        self.delivery_service.complete_delivery(delivery_id)
        
        # Update order status
        self.db.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": OrderStatus.DELIVERED,
                    "actual_delivery": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Order {order_id} delivered")
        return self.get_order(order_id)
    
    def cancel_order(self, order_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an order.
        
        If inventory was allocated, releases the reservation.
        """
        order = self.get_order(order_id)
        
        if order["status"] in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel order {order_id} in {order['status']} status")
        
        # If allocated, release inventory
        if order["status"] == OrderStatus.ALLOCATED and order.get("assigned_warehouse"):
            item = order["items"][0]
            self.inventory_service.release_allocation(
                order["assigned_warehouse"],
                item["sku"],
                item["quantity"]
            )
            
            # Cancel delivery if exists
            if order.get("delivery_id"):
                self.delivery_service.cancel_delivery(order["delivery_id"], reason)
        
        # Update order
        self.db.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": OrderStatus.CANCELLED,
                    "cancellation_reason": reason,
                    "cancelled_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Order {order_id} cancelled: {reason}")
        return self.get_order(order_id)
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order by ID"""
        order = self.db.orders.find_one({"order_id": order_id})
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return order
    
    def get_orders(
        self, 
        store_id: str = None, 
        status: str = None, 
        priority: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get orders with optional filters"""
        query = {}
        if store_id:
            query["store_id"] = store_id
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        
        return list(self.db.orders.find(query).sort("created_at", -1).limit(limit))
    
    def update_order_status(self, order_id: str, status: str) -> Dict[str, Any]:
        """Update order status (legacy method for compatibility)"""
        valid_statuses = [OrderStatus.PENDING, OrderStatus.ALLOCATED, OrderStatus.SHIPPED, 
                         OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.FAILED]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == OrderStatus.DELIVERED:
            update_data["actual_delivery"] = datetime.utcnow()
        
        result = self.db.orders.update_one(
            {"order_id": order_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Order {order_id} not found")
        
        return self.get_order(order_id)
    
    def get_order_stats(self) -> Dict[str, Any]:
        """Get order statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$total_amount"}
                }
            }
        ]
        
        status_stats = list(self.db.orders.aggregate(pipeline))
        
        return {
            "by_status": {item["_id"]: {"count": item["count"], "total": item["total_amount"]} for item in status_stats},
            "total_orders": sum(item["count"] for item in status_stats),
            "total_revenue": sum(item["total_amount"] for item in status_stats)
        }
    
    def _trigger_demand_check(self):
        """
        Trigger demand pattern check after order creation.
        This is an event-driven hook for the Sensing & Intelligence Layer.
        """
        try:
            from services.sensing_service import sensing_service
            # Check for demand spikes (this is lightweight as it uses cached data)
            sensing_service.detect_demand_spike(source="event_trigger")
        except ImportError:
            logger.debug("Sensing service not available for event trigger")
        except Exception as e:
            logger.warning(f"Error in demand check trigger: {e}")
