"""
Execution Agent - Handles action execution and workflow management

Part of the multi-agent orchestration system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.connection import mongodb
import logging
import uuid

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """
    Agent responsible for executing orchestration actions.

    Capabilities:
    - Execute validated actions
    - Track execution status
    - Handle rollbacks
    - Log execution history
    """

    AGENT_NAME = "execution_agent"
    AGENT_TYPE = "execution"

    # Supported action types
    ACTION_HANDLERS = {
        "replenish_inventory": "_handle_replenish_inventory",
        "transfer_inventory": "_handle_transfer_inventory",
        "reroute_delivery": "_handle_reroute_delivery",
        "change_delivery_priority": "_handle_change_priority",
        "reassign_warehouse": "_handle_reassign_warehouse",
        "rebalance_inventory": "_handle_rebalance_inventory",
        "escalate_alert": "_handle_escalate_alert",
        "no_action": "_handle_no_action"
    }

    def __init__(self):
        pass

    @property
    def db(self):
        return mongodb.get_database()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and identify execution capabilities.

        Args:
            context: Aggregated operational context

        Returns:
            Execution agent status and capabilities
        """
        try:
            logger.info("Execution Agent processing context")

            # Analyze execution readiness
            readiness = self._analyze_execution_readiness(context)

            # Get pending actions from decision service
            pending_actions = self._get_pending_actions()

            # Calculate execution capacity
            capacity = self._calculate_execution_capacity(pending_actions)

            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_readiness": readiness,
                "pending_actions": pending_actions[:10],
                "capacity": capacity,
                "supported_actions": list(self.ACTION_HANDLERS.keys()),
                "status": "ready"
            }

        except Exception as e:
            logger.error(f"Execution Agent error: {e}")
            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "status": "error",
                "error": str(e)
            }

    def _analyze_execution_readiness(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system readiness for action execution"""
        readiness = {
            "inventory_service": True,
            "warehouse_service": True,
            "delivery_service": True,
            "order_service": True,
            "overall": True
        }

        try:
            # Check if services are accessible
            services_to_check = ["inventory", "warehouses", "deliveries", "orders"]

            for service in services_to_check:
                count = self.db[service].count_documents({})
                if count == 0:
                    readiness[f"{service}_service"] = False
                    readiness["overall"] = False

        except Exception as e:
            logger.error(f"Error analyzing execution readiness: {e}")
            readiness["overall"] = False

        return readiness

    def _get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get pending actions from various sources"""
        pending = []

        try:
            # Get pending replenishment orders
            replen_orders = list(self.db.replenishment_orders.find({
                "status": "pending_approval"
            }).limit(5))

            for order in replen_orders:
                pending.append({
                    "action_type": "replenish_inventory",
                    "source": "decision_service",
                    "order_id": order.get("order_id"),
                    "sku": order.get("items", [{}])[0].get("sku") if order.get("items") else None,
                    "quantity": order.get("items", [{}])[0].get("quantity") if order.get("items") else 0,
                    "warehouse_id": order.get("warehouse_id"),
                    "status": "pending_approval"
                })

        except Exception as e:
            logger.error(f"Error getting pending actions: {e}")

        return pending

    def _calculate_execution_capacity(self, pending_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate execution capacity"""
        return {
            "pending_count": len(pending_actions),
            "can_execute": len(pending_actions) < 10,
            "available_slots": max(0, 10 - len(pending_actions))
        }

    def execute_action(
        self,
        action: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a validated action.

        Args:
            action: Action to execute
            dry_run: If True, simulate without actual execution

        Returns:
            Execution result
        """
        action_type = action.get("action_type")
        execution_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Executing action {action_type} (execution_id: {execution_id})")

        result = {
            "execution_id": execution_id,
            "action_type": action_type,
            "timestamp": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
            "status": "pending"
        }

        try:
            # Get the handler for this action type
            handler_name = self.ACTION_HANDLERS.get(action_type)

            if not handler_name:
                raise ValueError(f"Unknown action type: {action_type}")

            handler = getattr(self, handler_name)

            if dry_run:
                # Simulate execution
                result.update({
                    "status": "simulated",
                    "message": f"Would execute {action_type}",
                    "action": action
                })
            else:
                # Execute for real
                execution_result = handler(action)
                result.update(execution_result)

            logger.info(f"Action {action_type} executed: {result.get('status')}")

        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            result.update({
                "status": "failed",
                "error": str(e)
            })

        return result

    def _handle_replenish_inventory(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory replenishment action"""
        try:
            from services.inventory_service import InventoryService
            from services.signal_service import signal_service

            sku = action.get("sku")
            warehouse_id = action.get("warehouse_id") or action.get("source_warehouse")
            quantity = action.get("quantity", 50)

            if not sku or not warehouse_id:
                raise ValueError("Missing sku or warehouse_id for replenishment")

            inventory_service = InventoryService()

            # Check if inventory record exists
            inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id
            })

            if inv:
                # Restock existing inventory
                result = inventory_service.restock_inventory(sku, warehouse_id, quantity)
            else:
                # Create new inventory record using upsert to avoid duplicates
                new_inv = {
                    "sku": sku,
                    "location_id": warehouse_id,
                    "location_type": "warehouse",
                    "current_stock": quantity,
                    "quantity": quantity,
                    "available_stock": quantity,
                    "reserved_stock": 0,
                    "incoming_stock": 0,
                    "damaged_stock": 0,
                    "reorder_threshold": 20,
                    "reorder_quantity": 50,
                    "transactions_count": 1,
                    "total_sales": 0,
                    "total_restock": quantity,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "last_restocked": datetime.utcnow()
                }
                # Use update with upsert to avoid duplicate key errors
                upsert_result = self.db.inventory.update_one(
                    {"sku": sku, "location_id": warehouse_id},
                    {"$setOnInsert": new_inv},
                    upsert=True
                )
                if not upsert_result.upserted_id:
                    # Record existed, update it instead
                    self.db.inventory.update_one(
                        {"sku": sku, "location_id": warehouse_id},
                        {"$inc": {"current_stock": quantity, "quantity": quantity, "total_restock": quantity},
                         "$set": {"updated_at": datetime.utcnow(), "last_restocked": datetime.utcnow()}}
                    )
                result = new_inv

            # Create transaction record
            txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            self.db.transactions.insert_one({
                "transaction_id": txn_id,
                "type": "restock",
                "sku": sku,
                "quantity": quantity,
                "location_id": warehouse_id,
                "location_type": "warehouse",
                "timestamp": datetime.utcnow(),
                "status": "completed",
                "trigger": "orchestration"
            })

            # Resolve related signals after successful replenishment
            resolved_signals = self._resolve_related_signals(sku, warehouse_id, quantity)

            return {
                "status": "success",
                "sku": sku,
                "warehouse_id": warehouse_id,
                "quantity_added": quantity,
                "transaction_id": txn_id,
                "resolved_signals": resolved_signals,
                "message": f"Replenished {quantity} units of {sku} at {warehouse_id}"
            }

        except Exception as e:
            logger.error(f"Error in replenish_inventory: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _resolve_related_signals(self, sku: str, warehouse_id: str, quantity_added: int) -> List[str]:
        """
        Resolve signals that are now fixed after replenishment.

        Args:
            sku: Product SKU
            warehouse_id: Location that was restocked
            quantity_added: Quantity that was added

        Returns:
            List of resolved signal IDs
        """
        resolved = []

        try:
            from services.signal_service import signal_service

            # Get current inventory level
            inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": warehouse_id
            })

            if not inv:
                return resolved

            current_stock = inv.get("current_stock", 0)

            # Find active signals for this SKU/location
            active_signals = signal_service.get_active_signals(
                entity_id=warehouse_id,
                limit=10
            )

            for signal in active_signals:
                signal_id = signal.get("signal_id")
                signal_type = signal.get("type")
                product_id = signal.get("product_id")
                details = signal.get("details", {})
                threshold = details.get("threshold", 20)

                # Check if signal is for this product
                if product_id != sku:
                    continue

                # Check if signal condition is resolved
                should_resolve = False
                resolution_note = ""

                if signal_type == "STOCKOUT" and current_stock > 0:
                    should_resolve = True
                    resolution_note = f"Stockout resolved - inventory now at {current_stock}"
                elif signal_type == "LOW_STOCK" and current_stock > threshold:
                    should_resolve = True
                    resolution_note = f"Low stock resolved - inventory now at {current_stock} (threshold: {threshold})"
                elif signal_type == "PREDICTED_STOCKOUT" and current_stock > 10:
                    should_resolve = True
                    resolution_note = f"Predicted stockout resolved - inventory now at {current_stock}"

                if should_resolve:
                    signal_service.resolve_signal(
                        signal_id,
                        auto_resolved=True,
                        action_taken={
                            "type": "llm_orchestration_replenishment",
                            "quantity_added": quantity_added,
                            "new_stock": current_stock
                        },
                        resolution_note=resolution_note
                    )
                    resolved.append(signal_id)
                    logger.info(f"Auto-resolved signal {signal_id} after replenishment")

        except Exception as e:
            logger.error(f"Error resolving signals: {e}")

        return resolved

    def _handle_transfer_inventory(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle inventory transfer action"""
        try:
            sku = action.get("sku")
            source_wh = action.get("source_warehouse")
            target_wh = action.get("target_warehouse")
            quantity = action.get("quantity")

            if not all([sku, source_wh, target_wh, quantity]):
                raise ValueError("Missing required fields for transfer")

            # Check source inventory
            source_inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": source_wh
            })

            if not source_inv:
                raise ValueError(f"No inventory at source warehouse {source_wh}")

            available = source_inv.get("current_stock", 0) - source_inv.get("reserved_stock", 0)
            if available < quantity:
                raise ValueError(f"Insufficient stock at source. Available: {available}, Required: {quantity}")

            # Reduce source
            self.db.inventory.update_one(
                {"_id": source_inv["_id"]},
                {
                    "$inc": {"current_stock": -quantity, "quantity": -quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            # Increase target
            target_inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": target_wh
            })

            if target_inv:
                self.db.inventory.update_one(
                    {"_id": target_inv["_id"]},
                    {
                        "$inc": {"current_stock": quantity, "quantity": quantity},
                        "$set": {"updated_at": datetime.utcnow(), "last_restocked": datetime.utcnow()}
                    }
                )
            else:
                # Create new inventory at target
                self.db.inventory.insert_one({
                    "sku": sku,
                    "location_id": target_wh,
                    "location_type": "warehouse",
                    "current_stock": quantity,
                    "quantity": quantity,
                    "reserved_stock": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })

            # Create transaction
            txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
            self.db.transactions.insert_one({
                "transaction_id": txn_id,
                "type": "transfer",
                "sku": sku,
                "quantity": quantity,
                "location_id": source_wh,
                "transfer_to": target_wh,
                "timestamp": datetime.utcnow(),
                "status": "completed",
                "trigger": "orchestration"
            })

            # Resolve signals at target location
            resolved_signals = self._resolve_related_signals(sku, target_wh, quantity)

            return {
                "status": "success",
                "sku": sku,
                "source_warehouse": source_wh,
                "target_warehouse": target_wh,
                "quantity_transferred": quantity,
                "transaction_id": txn_id,
                "resolved_signals": resolved_signals,
                "message": f"Transferred {quantity} units of {sku} from {source_wh} to {target_wh}"
            }

        except Exception as e:
            logger.error(f"Error in transfer_inventory: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_reroute_delivery(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery reroute action"""
        try:
            delivery_id = action.get("delivery_id")
            new_warehouse = action.get("new_warehouse_id")

            if not delivery_id:
                raise ValueError("Missing delivery_id")

            delivery = self.db.deliveries.find_one({"delivery_id": delivery_id})
            if not delivery:
                raise ValueError(f"Delivery {delivery_id} not found")

            # Update delivery with new route info
            update_data = {
                "updated_at": datetime.utcnow(),
                "rerouted": True,
                "original_warehouse_id": delivery.get("warehouse_id")
            }

            if new_warehouse:
                update_data["warehouse_id"] = new_warehouse

            self.db.deliveries.update_one(
                {"delivery_id": delivery_id},
                {"$set": update_data}
            )

            return {
                "status": "success",
                "delivery_id": delivery_id,
                "new_warehouse": new_warehouse,
                "message": f"Delivery {delivery_id} marked for reroute"
            }

        except Exception as e:
            logger.error(f"Error in reroute_delivery: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_change_priority(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery priority change"""
        try:
            delivery_id = action.get("delivery_id")
            new_priority = action.get("new_priority")

            if not delivery_id:
                raise ValueError("Missing delivery_id")

            self.db.deliveries.update_one(
                {"delivery_id": delivery_id},
                {
                    "$set": {
                        "priority": new_priority,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            return {
                "status": "success",
                "delivery_id": delivery_id,
                "new_priority": new_priority
            }

        except Exception as e:
            logger.error(f"Error in change_priority: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_reassign_warehouse(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle warehouse reassignment"""
        try:
            order_id = action.get("order_id")
            new_warehouse = action.get("new_warehouse_id")

            if not order_id:
                raise ValueError("Missing order_id")

            order = self.db.orders.find_one({"order_id": order_id})
            if not order:
                raise ValueError(f"Order {order_id} not found")

            old_warehouse = order.get("assigned_warehouse")

            # Update order
            self.db.orders.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "assigned_warehouse": new_warehouse,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Update associated delivery
            if order.get("delivery_id"):
                self.db.deliveries.update_one(
                    {"delivery_id": order["delivery_id"]},
                    {
                        "$set": {
                            "warehouse_id": new_warehouse,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

            return {
                "status": "success",
                "order_id": order_id,
                "old_warehouse": old_warehouse,
                "new_warehouse": new_warehouse
            }

        except Exception as e:
            logger.error(f"Error in reassign_warehouse: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_rebalance_inventory(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle inventory rebalance action.

        If specific SKU/location provided, do targeted replenishment.
        Otherwise, find and fix low stock items automatically.
        """
        try:
            sku = action.get("sku")
            target_wh = action.get("warehouse_id") or action.get("target_warehouse")
            quantity = action.get("quantity", 50)

            # If we have specific SKU and warehouse, do targeted replenishment
            if sku and target_wh:
                replenish_action = {
                    "sku": sku,
                    "warehouse_id": target_wh,
                    "quantity": quantity
                }
                return self._handle_replenish_inventory(replenish_action)

            # Otherwise, find low stock items and replenish them
            logger.info("No specific SKU/warehouse provided - finding low stock items to replenish")

            # Find inventory below reorder threshold
            low_stock_items = list(self.db.inventory.find({
                "$expr": {"$lt": ["$current_stock", "$reorder_threshold"]}
            }).limit(5))

            if not low_stock_items:
                return {
                    "status": "skipped",
                    "message": "No low stock items found"
                }

            results = []
            resolved_signals = []

            for item in low_stock_items:
                item_sku = item.get("sku")
                location = item.get("location_id")
                current = item.get("current_stock", 0)
                reorder_qty = item.get("reorder_quantity", 50)

                # Replenish this item
                replenish_result = self._handle_replenish_inventory({
                    "sku": item_sku,
                    "warehouse_id": location,
                    "quantity": reorder_qty
                })

                results.append({
                    "sku": item_sku,
                    "location": location,
                    "quantity_added": reorder_qty,
                    "status": replenish_result.get("status")
                })

                if replenish_result.get("resolved_signals"):
                    resolved_signals.extend(replenish_result.get("resolved_signals", []))

            return {
                "status": "success",
                "items_replenished": len(results),
                "details": results,
                "resolved_signals": resolved_signals,
                "message": f"Rebalanced {len(results)} low stock items"
            }

        except Exception as e:
            logger.error(f"Error in rebalance_inventory: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_escalate_alert(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert escalation"""
        try:
            signal_id = action.get("signal_id")

            if signal_id:
                # Create escalation record
                escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
                self.db.escalations.insert_one({
                    "escalation_id": escalation_id,
                    "signal_id": signal_id,
                    "created_at": datetime.utcnow(),
                    "status": "open"
                })

                return {
                    "status": "success",
                    "escalation_id": escalation_id
                }

            return {
                "status": "skipped",
                "message": "No signal_id provided"
            }

        except Exception as e:
            logger.error(f"Error in escalate_alert: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def _handle_no_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle no-action case"""
        return {
            "status": "skipped",
            "message": "No action required"
        }

    def rollback_action(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rollback a previously executed action.

        Args:
            execution_result: Previous execution result

        Returns:
            Rollback result
        """
        action_type = execution_result.get("action_type")
        rollback_id = f"ROLL-{uuid.uuid4().hex[:8].upper()}"

        logger.info(f"Rolling back action {action_type} (rollback_id: {rollback_id})")

        try:
            if action_type == "replenish_inventory":
                # Reverse the restock
                sku = execution_result.get("sku")
                warehouse_id = execution_result.get("warehouse_id")
                quantity = execution_result.get("quantity_added")

                if all([sku, warehouse_id, quantity]):
                    self.db.inventory.update_one(
                        {"sku": sku, "location_id": warehouse_id},
                        {"$inc": {"current_stock": -quantity, "quantity": -quantity},
                         "$set": {"updated_at": datetime.utcnow()}}
                    )

                return {
                    "status": "rolled_back",
                    "rollback_id": rollback_id
                }

            elif action_type == "transfer_inventory":
                # Reverse the transfer
                sku = execution_result.get("sku")
                source = execution_result.get("target_warehouse")
                target = execution_result.get("source_warehouse")
                quantity = execution_result.get("quantity_transferred")

                if all([sku, source, target, quantity]):
                    reverse_action = {
                        "sku": sku,
                        "source_warehouse": source,
                        "target_warehouse": target,
                        "quantity": quantity
                    }
                    return self._handle_transfer_inventory(reverse_action)

            return {
                "status": "not_reversible",
                "message": f"Cannot rollback action type: {action_type}"
            }

        except Exception as e:
            logger.error(f"Error rolling back action: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }


# Global instance
execution_agent = ExecutionAgent()
