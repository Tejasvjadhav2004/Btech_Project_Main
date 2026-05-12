"""
Decision Service - Decision engine for Sensing & Intelligence Layer

Processes signals and executes automated actions based on rules.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.connection import mongodb
from services.signal_service import SignalService, SignalType, SignalStatus
from api.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class ActionType:
    """Action type constants"""
    CREATE_REPLENISHMENT_ORDER = "create_replenishment_order"
    SEND_ALERT = "send_alert"
    ESCALATE = "escalate"
    LOG_WARNING = "log_warning"
    ADJUST_THRESHOLD = "adjust_threshold"
    NO_ACTION = "no_action"


class DecisionService:
    """
    Decision engine that processes signals and executes automated actions.
    
    Rules:
    - STOCKOUT → Create high-priority replenishment order + escalate
    - LOW_STOCK → Create replenishment order
    - DELIVERY_DELAY → Log alert, escalate if critical
    - DEMAND_SPIKE → Flag for review
    - OVER_UTILIZATION → Alert operations team
    """
    
    EVENT_LOGS_COLLECTION = "event_logs"
    
    # Action rules mapping signal types to actions
    ACTION_RULES = {
        SignalType.STOCKOUT: {
            "primary_action": ActionType.CREATE_REPLENISHMENT_ORDER,
            "secondary_action": ActionType.ESCALATE,
            "priority": "high",
            "auto_process": True
        },
        SignalType.LOW_STOCK: {
            "primary_action": ActionType.CREATE_REPLENISHMENT_ORDER,
            "secondary_action": ActionType.LOG_WARNING,
            "priority": "normal",
            "auto_process": True
        },
        SignalType.OVERSTOCK: {
            "primary_action": ActionType.LOG_WARNING,
            "secondary_action": None,
            "priority": "low",
            "auto_process": False
        },
        SignalType.DEMAND_SPIKE: {
            "primary_action": ActionType.SEND_ALERT,
            "secondary_action": ActionType.LOG_WARNING,
            "priority": "high",
            "auto_process": False
        },
        SignalType.DEMAND_DROP: {
            "primary_action": ActionType.LOG_WARNING,
            "secondary_action": None,
            "priority": "low",
            "auto_process": False
        },
        SignalType.DELIVERY_DELAY: {
            "primary_action": ActionType.SEND_ALERT,
            "secondary_action": ActionType.ESCALATE,
            "priority": "high",
            "auto_process": True
        },
        SignalType.OVER_UTILIZATION: {
            "primary_action": ActionType.SEND_ALERT,
            "secondary_action": ActionType.LOG_WARNING,
            "priority": "high",
            "auto_process": False
        },
        SignalType.UNDER_UTILIZATION: {
            "primary_action": ActionType.LOG_WARNING,
            "secondary_action": None,
            "priority": "low",
            "auto_process": False
        }
    }
    
    # Default replenishment quantities based on product category
    DEFAULT_REPLENISHMENT_QTY = 50
    
    def __init__(self):
        # Don't cache database reference - get it dynamically each time
        pass
    
    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()
    
    @property
    def signal_service(self):
        """Get signal service dynamically"""
        from services.signal_service import SignalService
        return SignalService()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"EVT-{uuid.uuid4().hex[:8].upper()}"
    
    def _log_action(
        self,
        signal_id: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ):
        """Log an action to event_logs collection"""
        try:
            event = {
                "event_id": self._generate_event_id(),
                "signal_id": signal_id,
                "event_type": "action_executed",
                "action": action,
                "status": status,
                "source": "decision_engine",
                "metadata": metadata or {},
                "error": error,
                "timestamp": datetime.utcnow()
            }
            
            self.db[self.EVENT_LOGS_COLLECTION].insert_one(event)
            logger.info(f"Action logged: {action} for signal {signal_id} - {status}")
        except Exception as e:
            logger.error(f"Error logging action: {e}")
    
    def process_signal(self, signal_id: str) -> Dict[str, Any]:
        """
        Process a signal and execute appropriate actions.
        
        Args:
            signal_id: ID of the signal to process
        
        Returns:
            Result of the processing with action details
        """
        try:
            # Get signal
            signal = self.signal_service.get_signal(signal_id)
            
            if not signal:
                return {
                    "success": False,
                    "error": f"Signal {signal_id} not found"
                }
            
            if signal["status"] != SignalStatus.ACTIVE:
                return {
                    "success": False,
                    "error": f"Signal {signal_id} is not active (status: {signal['status']})"
                }
            
            signal_type = signal["type"]
            
            # Get action rules
            rules = self.ACTION_RULES.get(signal_type, {
                "primary_action": ActionType.LOG_WARNING,
                "auto_process": False
            })
            
            # Execute primary action
            action_result = self._execute_action(
                signal=signal,
                action_type=rules["primary_action"],
                priority=rules.get("priority", "normal")
            )
            
            # Execute secondary action if present
            secondary_result = None
            if rules.get("secondary_action"):
                secondary_result = self._execute_action(
                    signal=signal,
                    action_type=rules["secondary_action"],
                    priority=rules.get("priority", "normal")
                )
            
            # Acknowledge signal after processing
            self.signal_service.acknowledge_signal(signal_id)
            
            result = {
                "success": True,
                "signal_id": signal_id,
                "signal_type": signal_type,
                "primary_action": action_result,
                "secondary_action": secondary_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed signal {signal_id}: {signal_type} -> {rules['primary_action']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing signal {signal_id}: {e}")
            return {
                "success": False,
                "signal_id": signal_id,
                "error": str(e)
            }
    
    def _execute_action(
        self,
        signal: Dict[str, Any],
        action_type: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Execute a specific action for a signal.
        
        Args:
            signal: Signal document
            action_type: Type of action to execute
            priority: Action priority
        
        Returns:
            Action execution result
        """
        signal_id = signal["signal_id"]
        signal_type = signal["type"]
        
        try:
            if action_type == ActionType.CREATE_REPLENISHMENT_ORDER:
                return self._create_replenishment_order(signal, priority)
            
            elif action_type == ActionType.SEND_ALERT:
                return self._send_alert(signal, priority)
            
            elif action_type == ActionType.ESCALATE:
                return self._escalate(signal)
            
            elif action_type == ActionType.LOG_WARNING:
                return self._log_warning(signal)
            
            elif action_type == ActionType.NO_ACTION:
                return {
                    "action": ActionType.NO_ACTION,
                    "status": "success",
                    "message": "No action required"
                }
            
            else:
                return {
                    "action": action_type,
                    "status": "skipped",
                    "message": f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            error_info = {"error": str(e), "action_type": action_type}
            self._log_action(signal_id, action_type, "failed", error=error_info)
            return {
                "action": action_type,
                "status": "failed",
                "error": str(e)
            }
    
    def _create_replenishment_order(
        self,
        signal: Dict[str, Any],
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Create a replenishment order for low stock or stockout signals.

        This creates an order from a supplier to replenish warehouse stock.
        Uses real data from inventory (reorder_threshold, reorder_quantity) and products (price).
        """
        signal_id = signal["signal_id"]
        details = signal.get("details", {})

        sku = details.get("sku")
        warehouse_id = signal.get("entity_id")
        current_stock = details.get("available_stock", 0)
        threshold = details.get("threshold", settings.low_stock_threshold)

        if not sku or not warehouse_id:
            return {
                "action": ActionType.CREATE_REPLENISHMENT_ORDER,
                "status": "failed",
                "error": "Missing SKU or warehouse_id in signal details"
            }

        # Get inventory record for real reorder_quantity and reorder_threshold
        inventory_record = self.db.inventory.find_one({
            "sku": sku,
            "location_id": warehouse_id
        })

        # Use real values from inventory if available
        if inventory_record:
            reorder_quantity = inventory_record.get("reorder_quantity", 50)
            reorder_threshold = inventory_record.get("reorder_threshold", threshold)
            optimal_stock = inventory_record.get("optimal_stock")
        else:
            reorder_quantity = 50
            reorder_threshold = threshold
            optimal_stock = None

        # Calculate replenishment quantity using real data
        # Priority: optimal_stock > reorder_quantity > calculated
        if optimal_stock and optimal_stock > current_stock:
            replenishment_qty = optimal_stock - current_stock
        else:
            # Calculate to bring stock to 3x threshold or use reorder_quantity
            target_stock = max(reorder_threshold * 3, current_stock + reorder_quantity)
            replenishment_qty = max(reorder_quantity, target_stock - current_stock)

        # Get product price for unit_price
        product = self.db.products.find_one({"sku": sku})
        unit_price = product.get("current_price", 0) if product else 0

        # Find a supplier for this product
        supplier = self.db.suppliers.find_one(
            {"products": {"$in": [sku]}} if sku else {}
        )
        if not supplier:
            supplier = self.db.suppliers.find_one()

        supplier_id = supplier["supplier_id"] if supplier else "SUP-DEFAULT"

        # Create replenishment order
        order_id = f"REPL-{uuid.uuid4().hex[:8].upper()}"

        replenishment_order = {
            "order_id": order_id,
            "order_type": "replenishment",
            "triggered_by_signal": signal_id,
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "items": [{
                "sku": sku,
                "quantity": replenishment_qty,
                "unit_price": unit_price,
                "total_price": unit_price * replenishment_qty
            }],
            "total_amount": unit_price * replenishment_qty,
            "status": "pending_approval",
            "priority": "high" if signal["type"] == SignalType.STOCKOUT else priority,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "auto_generated": True,
            "notes": f"Auto-generated from signal {signal_id}",
            "calculation_details": {
                "current_stock": current_stock,
                "reorder_threshold": reorder_threshold,
                "reorder_quantity_used": reorder_quantity,
                "optimal_stock": optimal_stock,
                "calculated_replenishment_qty": replenishment_qty
            }
        }
        
        # Insert into orders collection (or a separate replenishment_orders collection)
        result = self.db.replenishment_orders.insert_one(replenishment_order)
        
        # Log the action
        self._log_action(
            signal_id=signal_id,
            action=ActionType.CREATE_REPLENISHMENT_ORDER,
            status="success",
            metadata={
                "order_id": order_id,
                "sku": sku,
                "quantity": replenishment_qty,
                "warehouse_id": warehouse_id,
                "supplier_id": supplier_id
            }
        )
        
        logger.info(
            f"Created replenishment order {order_id}: {replenishment_qty}x {sku} "
            f"for warehouse {warehouse_id}"
        )
        
        return {
            "action": ActionType.CREATE_REPLENISHMENT_ORDER,
            "status": "success",
            "order_id": order_id,
            "sku": sku,
            "quantity": replenishment_qty,
            "warehouse_id": warehouse_id,
            "supplier_id": supplier_id
        }
    
    def _send_alert(self, signal: Dict[str, Any], priority: str) -> Dict[str, Any]:
        """
        Send an alert for the signal.
        
        In a production system, this would integrate with notification services
        (email, Slack, PagerDuty, etc.). For now, we log it.
        """
        signal_id = signal["signal_id"]
        signal_type = signal["type"]
        severity = signal["severity"]
        message = signal["message"]
        
        # Create alert record
        alert = {
            "alert_id": f"ALT-{uuid.uuid4().hex[:8].upper()}",
            "signal_id": signal_id,
            "signal_type": signal_type,
            "severity": severity,
            "priority": priority,
            "message": message,
            "details": signal.get("details", {}),
            "channels": ["dashboard", "log"],  # Future: email, slack, etc.
            "acknowledged": False,
            "created_at": datetime.utcnow()
        }
        
        # Store alert
        self.db.alerts.insert_one(alert)
        
        # Log the action
        self._log_action(
            signal_id=signal_id,
            action=ActionType.SEND_ALERT,
            status="success",
            metadata={
                "alert_id": alert["alert_id"],
                "severity": severity,
                "priority": priority,
                "channels": alert["channels"]
            }
        )
        
        logger.warning(
            f"ALERT [{severity.upper()}]: {message} (Signal: {signal_id})"
        )
        
        return {
            "action": ActionType.SEND_ALERT,
            "status": "success",
            "alert_id": alert["alert_id"],
            "severity": severity,
            "message": message
        }
    
    def _escalate(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Escalate a signal to higher priority handling.
        """
        signal_id = signal["signal_id"]
        severity = signal["severity"]
        
        # Create escalation record
        escalation = {
            "escalation_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
            "signal_id": signal_id,
            "original_severity": severity,
            "escalation_level": 1,
            "reason": f"Automatic escalation for {signal['type']}",
            "assigned_to": "operations_team",  # Future: actual user/team assignment
            "status": "open",
            "created_at": datetime.utcnow()
        }
        
        self.db.escalations.insert_one(escalation)
        
        # Log the action
        self._log_action(
            signal_id=signal_id,
            action=ActionType.ESCALATE,
            status="success",
            metadata={
                "escalation_id": escalation["escalation_id"],
                "escalation_level": 1,
                "assigned_to": escalation["assigned_to"]
            }
        )
        
        logger.warning(
            f"ESCALATION: Signal {signal_id} escalated to operations_team"
        )
        
        return {
            "action": ActionType.ESCALATE,
            "status": "success",
            "escalation_id": escalation["escalation_id"],
            "assigned_to": escalation["assigned_to"]
        }
    
    def _log_warning(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a warning for the signal without taking automated action.
        """
        signal_id = signal["signal_id"]
        
        self._log_action(
            signal_id=signal_id,
            action=ActionType.LOG_WARNING,
            status="success",
            metadata={
                "type": signal["type"],
                "severity": signal["severity"],
                "message": signal["message"]
            }
        )
        
        logger.warning(
            f"Warning logged for signal {signal_id}: {signal['message']}"
        )
        
        return {
            "action": ActionType.LOG_WARNING,
            "status": "success",
            "message": "Warning logged"
        }
    
    def process_active_signals(self, auto_only: bool = True) -> Dict[str, Any]:
        """
        Process all active signals.
        
        Args:
            auto_only: If True, only process signals marked for auto-processing
        
        Returns:
            Summary of processing results
        """
        try:
            active_signals = self.signal_service.get_active_signals()
            
            results = {
                "processed": 0,
                "skipped": 0,
                "failed": 0,
                "details": []
            }
            
            for signal in active_signals:
                signal_type = signal["type"]
                rules = self.ACTION_RULES.get(signal_type, {})
                
                # Skip if auto_only and signal type is not auto-processable
                if auto_only and not rules.get("auto_process", False):
                    results["skipped"] += 1
                    continue
                
                result = self.process_signal(signal["signal_id"])
                
                if result.get("success"):
                    results["processed"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "signal_id": signal["signal_id"],
                    "type": signal_type,
                    "result": result
                })
            
            results["total"] = len(active_signals)
            results["timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(
                f"Processed {results['processed']} signals, "
                f"skipped {results['skipped']}, failed {results['failed']}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing active signals: {e}")
            raise
    
    def get_pending_replenishment_orders(self) -> List[Dict[str, Any]]:
        """Get all pending replenishment orders"""
        try:
            orders = list(self.db.replenishment_orders.find({
                "status": "pending_approval"
            }).sort("created_at", -1))
            
            for order in orders:
                order["id"] = str(order.pop("_id"))
            
            return orders
        except Exception as e:
            logger.error(f"Error fetching pending replenishment orders: {e}")
            return []
    
    def approve_replenishment_order(self, order_id: str) -> Dict[str, Any]:
        """
        Approve a replenishment order and execute the restocking.

        This:
        1. Updates order status to 'approved'
        2. Adds stock to the warehouse inventory
        3. Updates warehouse utilization
        4. Resolves related signals if stock is now above threshold
        5. Creates a transaction record
        """
        # Get the order
        order = self.db.replenishment_orders.find_one({"order_id": order_id})
        if not order:
            return {"success": False, "error": "Order not found"}

        if order["status"] != "pending_approval":
            return {"success": False, "error": f"Order already {order['status']}"}

        warehouse_id = order["warehouse_id"]
        items = order.get("items", [])
        signal_id = order.get("triggered_by_signal")

        updated_inventory = []
        resolved_signals = []

        # Process each item in the order
        for item in items:
            sku = item["sku"]
            quantity = item["quantity"]

            # Find inventory record for this SKU at this location
            # Note: location could be warehouse or store, so don't filter by location_type
            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id
            })

            if inventory:
                # Update inventory stock
                old_stock = inventory.get("current_stock", inventory.get("quantity", 0))
                old_available = inventory.get("available_stock", old_stock - inventory.get("reserved_stock", 0))
                new_stock = old_stock + quantity
                new_available = old_available + quantity

                # Update inventory record
                self.db.inventory.update_one(
                    {"_id": inventory["_id"]},
                    {
                        "$set": {
                            "current_stock": new_stock,
                            "available_stock": new_available,
                            "quantity": new_stock,
                            "last_restocked": datetime.utcnow(),
                            "last_updated": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        },
                        "$inc": {
                            "total_restock": quantity
                        }
                    }
                )

                updated_inventory.append({
                    "sku": sku,
                    "old_stock": old_stock,
                    "new_stock": new_stock,
                    "quantity_added": quantity
                })

                logger.info(f"Restocked {quantity} units of {sku} at {warehouse_id} (was {old_stock}, now {new_stock})")
            else:
                # Create new inventory record if doesn't exist
                new_inventory = {
                    "sku": sku,
                    "location_id": warehouse_id,
                    "location_type": "warehouse",
                    "current_stock": quantity,
                    "available_stock": quantity,
                    "reserved_stock": 0,
                    "initial_stock": quantity,
                    "quantity": quantity,
                    "incoming_stock": 0,
                    "damaged_stock": 0,
                    "transactions_count": 1,
                    "total_sales": 0,
                    "total_restock": quantity,
                    "reorder_threshold": 20,
                    "reorder_quantity": 50,
                    "last_restocked": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                # Use update with upsert to avoid duplicate key errors
                result = self.db.inventory.update_one(
                    {"sku": sku, "location_id": warehouse_id},
                    {
                        "$setOnInsert": new_inventory,
                        "$inc": {"total_restock": quantity}
                    },
                    upsert=True
                )

                if result.upserted_id:
                    logger.info(f"Created new inventory record: {quantity} units of {sku} at {warehouse_id}")
                else:
                    # Record already existed (race condition), just update it
                    self.db.inventory.update_one(
                        {"sku": sku, "location_id": warehouse_id},
                        {
                            "$inc": {
                                "current_stock": quantity,
                                "available_stock": quantity,
                                "quantity": quantity
                            },
                            "$set": {
                                "last_restocked": datetime.utcnow(),
                                "last_updated": datetime.utcnow(),
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                    logger.info(f"Updated existing inventory record (race condition): {quantity} units of {sku} at {warehouse_id}")

                updated_inventory.append({
                    "sku": sku,
                    "old_stock": 0,
                    "new_stock": quantity,
                    "quantity_added": quantity
                })

                logger.info(f"Created new inventory record: {quantity} units of {sku} at {warehouse_id}")

        # Update warehouse utilization
        self._update_warehouse_utilization(warehouse_id)

        # Resolve related signal if stock is now above threshold
        if signal_id:
            try:
                # Get the signal details to check threshold
                signal = self.signal_service.get_signal(signal_id)
                if signal and signal.get("status") in ["active", "acknowledged"]:
                    details = signal.get("details", {})
                    threshold = details.get("threshold", 20)
                    sku = items[0]["sku"] if items else None

                    if sku:
                        # Check current stock
                        inv = self.db.inventory.find_one({
                            "sku": sku,
                            "location_id": warehouse_id
                        })
                        current_stock = inv.get("current_stock", 0) if inv else 0

                        if current_stock > threshold:
                            # Auto-resolve the signal
                            self.signal_service.resolve_signal(
                                signal_id,
                                auto_resolved=True,
                                action_taken={
                                    "type": "replenishment_approved",
                                    "order_id": order_id,
                                    "quantity_added": items[0]["quantity"] if items else 0,
                                    "new_stock": current_stock
                                }
                            )
                            resolved_signals.append(signal_id)
                            logger.info(f"Auto-resolved signal {signal_id} - stock now above threshold")
            except Exception as e:
                logger.warning(f"Could not auto-resolve signal {signal_id}: {e}")

        # Create transaction record
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        transaction = {
            "transaction_id": transaction_id,
            "type": "restock",
            "sku": items[0]["sku"] if items else None,
            "quantity": sum(item["quantity"] for item in items),
            "location_id": warehouse_id,
            "location_type": "warehouse",
            "order_id": order_id,
            "supplier_id": order.get("supplier_id"),
            "timestamp": datetime.utcnow(),
            "status": "completed",
            "notes": f"Replenishment order {order_id} approved"
        }
        self.db.transactions.insert_one(transaction)

        # Update order status to approved
        self.db.replenishment_orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": "approved",
                    "approved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "inventory_updates": updated_inventory,
                    "resolved_signals": resolved_signals,
                    "transaction_id": transaction_id
                }
            }
        )

        logger.info(f"Replenishment order {order_id} approved and executed successfully")

        return {
            "success": True,
            "order_id": order_id,
            "status": "approved",
            "inventory_updated": updated_inventory,
            "signals_resolved": resolved_signals,
            "transaction_id": transaction_id,
            "message": f"Restocked {sum(i['quantity'] for i in items)} units at {warehouse_id}"
        }

    def _update_warehouse_utilization(self, warehouse_id: str):
        """Recalculate and update warehouse utilization after restocking"""
        try:
            # Sum all inventory at this warehouse
            pipeline = [
                {"$match": {"location_id": warehouse_id, "location_type": "warehouse"}},
                {"$group": {"_id": None, "total": {"$sum": "$current_stock"}}}
            ]
            result = list(self.db.inventory.aggregate(pipeline))
            total_stock = result[0]["total"] if result else 0

            # Update warehouse
            self.db.warehouses.update_one(
                {"warehouse_id": warehouse_id},
                {
                    "$set": {
                        "current_utilization": total_stock,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated warehouse {warehouse_id} utilization to {total_stock}")
        except Exception as e:
            logger.error(f"Error updating warehouse utilization: {e}")
    
    def get_alerts(
        self,
        acknowledged: bool = None,
        severity: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alerts with optional filters"""
        logger.info(f"get_alerts called with: acknowledged={acknowledged}, severity={severity}, limit={limit}")
        query = {}

        if acknowledged is not None:
            query["acknowledged"] = acknowledged
        if severity:
            query["severity"] = severity

        logger.info(f"Query: {query}")

        try:
            logger.info(f"Attempting to query alerts collection...")
            alerts = list(self.db.alerts.find(query).sort("created_at", -1).limit(limit))
            logger.info(f"Found {len(alerts)} alerts")

            for alert in alerts:
                alert["id"] = str(alert.pop("_id"))

            return alerts
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        result = self.db.alerts.update_one(
            {"alert_id": alert_id},
            {
                "$set": {
                    "acknowledged": True,
                    "acknowledged_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {"success": True, "alert_id": alert_id}
        
        return {"success": False, "error": "Alert not found"}
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get decision engine statistics"""
        # Count actions by type
        pipeline = [
            {"$match": {"event_type": "action_executed"}},
            {
                "$group": {
                    "_id": "$action",
                    "count": {"$sum": 1},
                    "success_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    }
                }
            }
        ]
        
        action_stats = list(self.db[self.EVENT_LOGS_COLLECTION].aggregate(pipeline))
        
        # Count pending replenishment orders
        pending_orders = self.db.replenishment_orders.count_documents({
            "status": "pending_approval"
        })
        
        # Count unacknowledged alerts
        unack_alerts = self.db.signals.count_documents({"acknowledged": False})
        
        # Count open escalations
        open_escalations = self.db.escalations.count_documents({"status": "open"})
        
        return {
            "actions_by_type": {item["_id"]: item for item in action_stats},
            "pending_replenishment_orders": pending_orders,
            "unacknowledged_alerts": unack_alerts,
            "open_escalations": open_escalations
        }


# Global decision service instance
decision_service = DecisionService()
