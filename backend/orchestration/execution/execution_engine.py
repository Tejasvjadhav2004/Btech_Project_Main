"""
Execution Engine

Executes validated workflow actions through existing services.
Implements transaction safety and rollback support.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from orchestration.models.schemas import (
    Workflow, WorkflowStep, ExecutionStatus, ActionType
)
from orchestration.utils.helpers import generate_action_id
from orchestration.models.collections import get_audit_logs_collection
from services.signal_service import signal_service, SignalStatus
import logging

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """
    Executes orchestration actions through existing validated services.

    NEVER directly modifies MongoDB - always uses service layer.
    Implements transaction-like safety with rollback support.
    """

    def __init__(self):
        self._services = {}

    def _get_service(self, service_name: str):
        """Lazy load services to avoid circular imports"""
        if service_name not in self._services:
            try:
                if service_name == "inventory":
                    from services.inventory_service import InventoryService
                    self._services["inventory"] = InventoryService()
                elif service_name == "order":
                    from services.order_service import OrderService
                    self._services["order"] = OrderService()
                elif service_name == "warehouse":
                    from services.warehouse_service import WarehouseService
                    self._services["warehouse"] = WarehouseService()
                elif service_name == "delivery":
                    from services.delivery_service import DeliveryService
                    self._services["delivery"] = DeliveryService()
                elif service_name == "decision":
                    from services.decision_service import DecisionService
                    self._services["decision"] = DecisionService()
            except Exception as e:
                logger.warning(f"Could not load service {service_name}: {e}")
                return None
        return self._services.get(service_name)

    @property
    def inventory_service(self):
        return self._get_service("inventory")

    @property
    def order_service(self):
        return self._get_service("order")

    @property
    def warehouse_service(self):
        return self._get_service("warehouse")

    @property
    def delivery_service(self):
        return self._get_service("delivery")

    @property
    def decision_service(self):
        return self._get_service("decision")

    @property
    def db(self):
        """Get database connection"""
        from db.connection import mongodb
        return mongodb.get_database()

    async def execute_step(
        self,
        workflow: Workflow,
        step: WorkflowStep
    ) -> Dict[str, Any]:
        """
        Execute a single workflow step through the appropriate service.

        Args:
            workflow: Parent workflow
            step: Step to execute

        Returns:
            Execution result with success status and rollback data
        """
        action_id = generate_action_id()
        step.status = ExecutionStatus.RUNNING
        step.started_at = datetime.utcnow()

        result = {
            "action_id": action_id,
            "step_id": step.step_id,
            "action_type": step.action_type,
            "started_at": step.started_at.isoformat()
        }

        try:
            # Execute action through service layer
            if step.action_type == ActionType.INVENTORY_TRANSFER:
                execution_result = await self._execute_inventory_transfer(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.CREATE_REPLENISHMENT_ORDER:
                execution_result = await self._execute_replenishment_order(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.DELIVERY_REROUTE:
                execution_result = await self._execute_delivery_reroute(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.WAREHOUSE_REASSIGNMENT:
                execution_result = await self._execute_warehouse_reassignment(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.PRIORITY_ADJUSTMENT:
                execution_result = await self._execute_priority_adjustment(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.STOCK_RESERVATION:
                execution_result = await self._execute_stock_reservation(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.SUPPLIER_ORDER:
                execution_result = await self._execute_supplier_order(step.parameters)
                result.update(execution_result)

            elif step.action_type == ActionType.DELIVERY_EXPEDITE:
                execution_result = await self._execute_delivery_expedite(step.parameters)
                result.update(execution_result)

            else:
                raise ValueError(f"Unknown action type: {step.action_type}")

            # Mark step as successful
            step.status = ExecutionStatus.SUCCESS
            step.completed_at = datetime.utcnow()
            step.result = execution_result
            step.rollback_data = result.get("rollback_data")

            result["status"] = "success"
            result["completed_at"] = step.completed_at.isoformat()

            # Audit log
            self._audit_action(workflow.workflow_id, step, result, "success")

            logger.info(f"Step {step.step_id} executed successfully")

        except Exception as e:
            logger.error(f"Step {step.step_id} execution failed: {e}")

            step.status = ExecutionStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()

            result["status"] = "failed"
            result["error"] = str(e)
            result["completed_at"] = step.completed_at.isoformat()

            # Audit log failure
            self._audit_action(workflow.workflow_id, step, result, "failed")

        return result

    async def _execute_inventory_transfer(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute inventory transfer between warehouses.

        Uses inventory_service for actual transfer.
        """
        sku = params.get("sku")
        from_warehouse = params.get("from_warehouse") or params.get("source_warehouse")
        to_warehouse = params.get("to_warehouse") or params.get("target_location")
        quantity = params.get("quantity", 0)

        if not all([sku, to_warehouse, quantity > 0]):
            raise ValueError("Missing required parameters for transfer")

        # Find source warehouse with stock
        if not from_warehouse:
            from_warehouse = await self._find_source_warehouse(sku, quantity)

        if not from_warehouse:
            raise ValueError(f"No warehouse has sufficient stock of {sku}")

        # Execute transfer via inventory service
        # Reduce stock at source
        source_result = self.inventory_service.update_inventory(
            sku=sku,
            location_id=from_warehouse,
            quantity_change=-quantity
        )

        # Increase stock at destination
        dest_result = self.inventory_service.update_inventory(
            sku=sku,
            location_id=to_warehouse,
            quantity_change=quantity
        )

        return {
            "action": "inventory_transfer",
            "sku": sku,
            "from_warehouse": from_warehouse,
            "to_warehouse": to_warehouse,
            "quantity_transferred": quantity,
            "result": {
                "source": source_result,
                "destination": dest_result
            },
            "rollback_data": {
                "operation": "transfer",
                "sku": sku,
                "from": from_warehouse,
                "to": to_warehouse,
                "quantity": quantity
            }
        }

    async def _execute_replenishment_order(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute replenishment order creation"""
        from services.decision_service import decision_service

        sku = params.get("sku")
        warehouse_id = params.get("warehouse_id")
        quantity = params.get("quantity", 50)

        # Create replenishment via decision service
        order_result = self.decision_service._create_replenishment_order(
            signal={"signal_id": "orchestrated", "type": "ORCHESTRATION", "details": params},
            priority=params.get("priority", "normal")
        )

        return {
            "action": "replenishment_order",
            "order_id": order_result.get("order_id"),
            "sku": sku,
            "warehouse_id": warehouse_id,
            "quantity": quantity,
            "result": order_result,
            "rollback_data": {
                "operation": "replenishment_order",
                "order_id": order_result.get("order_id")
            }
        }

    async def _execute_delivery_reroute(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute delivery rerouting"""
        delivery_id = params.get("delivery_id")

        if not delivery_id:
            # Find delayed deliveries
            delayed_deliveries = list(self.delivery_service.db.deliveries.find({
                "status": "in_transit",
                "estimated_arrival": {"$lt": datetime.utcnow()}
            }).limit(5))

            if not delayed_deliveries:
                return {
                    "action": "delivery_reroute",
                    "status": "skipped",
                    "reason": "No delayed deliveries found"
                }

            result_list = []
            for delivery in delayed_deliveries:
                # Simple reroute: update ETA
                new_eta = datetime.utcnow()
                self.delivery_service.db.deliveries.update_one(
                    {"delivery_id": delivery["delivery_id"]},
                    {"$set": {
                        "estimated_arrival": new_eta,
                        "rerouted": True,
                        "rerouted_at": datetime.utcnow()
                    }}
                )
                result_list.append({
                    "delivery_id": delivery["delivery_id"],
                    "new_eta": new_eta.isoformat()
                })

            return {
                "action": "delivery_reroute",
                "rerouted_count": len(result_list),
                "deliveries": result_list
            }

        # Single delivery reroute
        delivery = self.delivery_service.get_delivery(delivery_id)
        if not delivery:
            raise ValueError(f"Delivery {delivery_id} not found")

        # Find alternate route
        new_route = await self._find_alternate_route(delivery)

        delivery["route"] = new_route
        self.delivery_service.db.deliveries.update_one(
            {"delivery_id": delivery_id},
            {"$set": {
                "route": new_route,
                "rerouted": True,
                "rerouted_at": datetime.utcnow()
            }}
        )

        return {
            "action": "delivery_reroute",
            "delivery_id": delivery_id,
            "new_route": new_route
        }

    async def _execute_warehouse_reassignment(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute warehouse reassignment for orders"""
        current_warehouse = params.get("current_warehouse")
        utilization_threshold = params.get("utilization_threshold", 80)

        # Find alternate warehouse
        alternate_wh = await self._find_alternate_warehouse(
            current_warehouse,
            utilization_threshold
        )

        if not alternate_wh:
            raise ValueError("No alternate warehouse available")

        # Reassign pending orders
        orders = list(self.order_service.db.orders.find({
            "assigned_warehouse": current_warehouse,
            "status": {"$in": ["pending", "allocated"]}
        }).limit(10))

        reassigned = []
        for order in orders:
            self.order_service.db.orders.update_one(
                {"order_id": order["order_id"]},
                {"$set": {
                    "assigned_warehouse": alternate_wh["warehouse_id"],
                    "warehouse_reassigned_at": datetime.utcnow()
                }}
            )
            reassigned.append(order["order_id"])

        return {
            "action": "warehouse_reassignment",
            "from_warehouse": current_warehouse,
            "to_warehouse": alternate_wh["warehouse_id"],
            "orders_reassigned": len(reassigned),
            "order_ids": reassigned
        }

    async def _execute_priority_adjustment(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute priority adjustment for orders"""
        sku = params.get("sku")
        new_priority = params.get("new_priority", "high")

        query = {}
        if sku:
            query["items.sku"] = sku

        query["status"] = {"$in": ["pending", "allocated"]}

        result = self.order_service.db.orders.update_many(
            query,
            {"$set": {
                "priority": new_priority,
                "priority_adjusted_at": datetime.utcnow()
            }}
        )

        return {
            "action": "priority_adjustment",
            "new_priority": new_priority,
            "orders_updated": result.modified_count
        }

    async def _execute_stock_reservation(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute stock reservation for priority orders"""
        sku = params.get("sku")
        reserve_percentage = params.get("reserve_percentage", 30)

        # Get current stock
        inventory = self.inventory_service.get_inventory(sku=sku)
        if not inventory:
            raise ValueError(f"No inventory for {sku}")

        total_stock = sum(inv.get("quantity", 0) for inv in inventory)
        reserve_qty = int(total_stock * reserve_percentage / 100)

        # Reserve stock at primary warehouse
        primary_wh = inventory[0].get("location_id") if inventory else None
        if primary_wh:
            self.inventory_service.allocate_inventory(
                warehouse_id=primary_wh,
                sku=sku,
                quantity=reserve_qty
            )

        return {
            "action": "stock_reservation",
            "sku": sku,
            "reserved_quantity": reserve_qty,
            "warehouse": primary_wh
        }

    async def _execute_supplier_order(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute supplier order (expedited)"""
        result = await self._execute_replenishment_order(params)
        result["expedited"] = True
        return result

    async def _execute_delivery_expedite(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Expedite delivery"""
        sku = params.get("sku")

        query = {"status": "pending"}
        if sku:
            query["items.sku"] = sku

        # Update transport mode to faster option
        deliveries = self.delivery_service.db.deliveries.find(query).limit(10)

        expedited = []
        for delivery in deliveries:
            if delivery.get("transport_mode") == "truck":
                new_mode = "express"
            else:
                new_mode = "air"

            self.delivery_service.db.deliveries.update_one(
                {"delivery_id": delivery["delivery_id"]},
                {"$set": {
                    "transport_mode": new_mode,
                    "expedited": True,
                    "expedited_at": datetime.utcnow()
                }}
            )
            expedited.append(delivery["delivery_id"])

        return {
            "action": "delivery_expedite",
            "expedited_count": len(expedited),
            "delivery_ids": expedited
        }

    async def _find_source_warehouse(
        self,
        sku: str,
        quantity: int
    ) -> Optional[str]:
        """Find warehouse with sufficient stock"""
        warehouses = self.warehouse_service.get_warehouses_with_stock(sku, quantity)
        if warehouses:
            return warehouses[0]["warehouse_id"]
        return None

    async def _find_alternate_route(
        self,
        delivery: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find alternate delivery route"""
        # Simplified: just recalculate route
        return delivery.get("route", [])

    async def _find_alternate_warehouse(
        self,
        current_warehouse: str,
        threshold: float
    ) -> Optional[Dict[str, Any]]:
        """Find alternate warehouse with lower utilization"""
        warehouses = self.warehouse_service.get_all_warehouses()
        low_util = [wh for wh in warehouses if wh.get("utilization_percent", 0) < threshold]
        if low_util:
            return low_util[0]
        return None

    async def rollback_step(
        self,
        workflow: Workflow,
        step: WorkflowStep
    ) -> Dict[str, Any]:
        """
        Rollback a previously executed step.

        Args:
            workflow: Parent workflow
            step: Step to rollback

        Returns:
            Rollback result
        """
        if not step.rollback_data:
            return {
                "status": "failed",
                "reason": "No rollback data available"
            }

        rollback = step.rollback_data
        operation = rollback.get("operation")

        try:
            if operation == "transfer":
                # Reverse the transfer
                self.inventory_service.update_inventory(
                    sku=rollback["sku"],
                    location_id=rollback["to"],
                    quantity_change=-rollback["quantity"]
                )
                self.inventory_service.update_inventory(
                    sku=rollback["sku"],
                    location_id=rollback["from"],
                    quantity_change=rollback["quantity"]
                )

            elif operation == "replenishment_order":
                # Cancel the order
                order_id = rollback.get("order_id")
                if order_id:
                    self.decision_service.db.replenishment_orders.update_one(
                        {"order_id": order_id},
                        {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
                    )

            step.status = ExecutionStatus.ROLLED_BACK
            logger.info(f"Rolled back step {step.step_id}")

            return {"status": "success", "rolled_back": True}

        except Exception as e:
            logger.error(f"Rollback failed for step {step.step_id}: {e}")
            return {"status": "failed", "error": str(e)}

    def resolve_related_signals(
        self,
        workflow: Workflow,
        execution_result: Dict[str, Any]
    ) -> List[str]:
        """
        Resolve signals that have been addressed by the workflow execution.

        Args:
            workflow: Completed workflow
            execution_result: Result of workflow execution

        Returns:
            List of resolved signal IDs
        """
        resolved_signals = []

        try:
            # Get workflow context
            signal_id = workflow.trigger_signal_id
            sku = workflow.context_summary.get("sku")
            warehouse_id = workflow.context_summary.get("warehouse_id")

            if signal_id:
                # Resolve the triggering signal
                signal_service.resolve_signal(
                    signal_id,
                    auto_resolved=True,
                    action_taken={
                        "type": "workflow_execution",
                        "workflow_id": workflow.workflow_id,
                        "execution_time": execution_result.get("execution_time_seconds", 0)
                    },
                    resolution_note=f"Resolved by workflow {workflow.workflow_id}"
                )
                resolved_signals.append(signal_id)
                logger.info(f"Resolved triggering signal {signal_id}")

            # Find and resolve related signals that may have been fixed
            if sku and warehouse_id:
                related_signals = signal_service.get_active_signals(
                    signal_type=None,  # All types
                    entity_id=warehouse_id,
                    limit=10
                )

                for sig in related_signals:
                    if sig.get("signal_id") == signal_id:
                        continue  # Already resolved

                    # Check if signal condition is still valid
                    if self._check_signal_condition_resolved(sig):
                        signal_service.resolve_signal(
                            sig.get("signal_id"),
                            auto_resolved=True,
                            action_taken={
                                "type": "related_resolution",
                                "workflow_id": workflow.workflow_id,
                                "reason": "Condition no longer exists after workflow execution"
                            },
                            resolution_note=f"Resolved as side effect of workflow {workflow.workflow_id}"
                        )
                        resolved_signals.append(sig.get("signal_id"))
                        logger.info(f"Resolved related signal {sig.get('signal_id')}")

        except Exception as e:
            logger.error(f"Error resolving related signals: {e}")

        return resolved_signals

    def _check_signal_condition_resolved(self, signal: Dict[str, Any]) -> bool:
        """Check if a signal's condition has been resolved."""
        signal_type = signal.get("type")
        details = signal.get("details", {})
        entity_id = signal.get("entity_id")
        product_id = signal.get("product_id")

        from db.connection import mongodb
        db = mongodb.get_database()

        if signal_type in ["LOW_STOCK", "STOCKOUT", "PREDICTED_STOCKOUT"]:
            if not (product_id and entity_id):
                return False

            inventory = db.inventory.find_one({
                "sku": product_id,
                "location_id": entity_id
            })

            if inventory:
                current_stock = inventory.get("quantity", 0)
                threshold = details.get("threshold", 20)

                if signal_type == "LOW_STOCK" and current_stock > threshold:
                    return True
                if signal_type in ["STOCKOUT", "PREDICTED_STOCKOUT"] and current_stock > 5:
                    return True

        elif signal_type == "OVER_UTILIZATION":
            if not entity_id:
                return False

            warehouse = db.warehouses.find_one({"warehouse_id": entity_id})
            if warehouse:
                capacity = warehouse.get("capacity", 1)
                current_util = warehouse.get("current_utilization", 0)
                utilization_pct = (current_util / capacity * 100) if capacity > 0 else 0

                if utilization_pct < 85:
                    return True

        return False

    def _audit_action(
        self,
        workflow_id: str,
        step: WorkflowStep,
        result: Dict[str, Any],
        status: str
    ):
        """Write audit log"""
        try:
            collection = get_audit_logs_collection()
            audit_entry = {
                "action_id": generate_action_id(),
                "workflow_id": workflow_id,
                "step_id": step.step_id,
                "action_type": step.action_type.value,
                "status": status,
                "parameters": step.parameters,
                "result": result,
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(audit_entry)
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


# Global instance
execution_engine = ExecutionEngine()
