"""
Validation Service - Validates orchestration actions before execution

Ensures all actions are safe, valid, and executable.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db.connection import mongodb
from orchestration.schemas.action_schema import ActionSchema, ActionType, ValidationResult
import logging

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Validates orchestration decisions BEFORE execution.

    All LLM decisions must pass through validation before execution.
    """

    def __init__(self):
        self.validation_rules = {
            ActionType.REPLENISH_INVENTORY: self._validate_replenish,
            ActionType.TRANSFER_INVENTORY: self._validate_transfer,
            ActionType.REROUTE_DELIVERY: self._validate_reroute,
            ActionType.CHANGE_DELIVERY_PRIORITY: self._validate_priority_change,
            ActionType.REASSIGN_WAREHOUSE: self._validate_reassign,
            ActionType.REBALANCE_INVENTORY: self._validate_rebalance,
            ActionType.ESCALATE_ALERT: self._validate_escalate,
            ActionType.NO_ACTION: self._validate_no_action
        }

    @property
    def db(self):
        return mongodb.get_database()

    def validate_action(self, action: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single action.

        Args:
            action: Action to validate

        Returns:
            ValidationResult with status and any errors/warnings
        """
        action_type = action.get("action_type")
        action_id = action.get("action_id", f"action-{datetime.utcnow().timestamp()}")

        try:
            # First, validate against schema
            schema_errors = self._validate_schema(action)
            if schema_errors:
                return ValidationResult(
                    valid=False,
                    action_id=action_id,
                    action_type=action_type,
                    errors=schema_errors,
                    warnings=[]
                )

            # Get the appropriate validator
            validator = self.validation_rules.get(ActionType(action_type))
            if not validator:
                return ValidationResult(
                    valid=False,
                    action_id=action_id,
                    action_type=action_type,
                    errors=[f"Unknown action type: {action_type}"]
                )

            # Run specific validation
            return validator(action)

        except Exception as e:
            logger.error(f"Error validating action: {e}")
            return ValidationResult(
                valid=False,
                action_id=action_id,
                action_type=action_type,
                errors=[f"Validation error: {str(e)}"]
            )

    def validate_plan(self, actions: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate all actions in a plan.

        Args:
            actions: List of actions to validate

        Returns:
            List of validation results
        """
        results = []

        for i, action in enumerate(actions):
            if not action.get("action_id"):
                action["action_id"] = f"action-{i+1}"
            result = self.validate_action(action)
            results.append(result)

        return results

    def _validate_schema(self, action: Dict[str, Any]) -> List[str]:
        """Validate action against schema"""
        errors = []

        try:
            # Try to parse with Pydantic
            ActionSchema(**action)
        except Exception as e:
            errors.append(f"Schema validation failed: {str(e)}")

        return errors

    def _validate_replenish(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate replenish_inventory action"""
        errors = []
        warnings = []

        sku = action.get("sku")
        warehouse_id = action.get("warehouse_id") or action.get("source_warehouse")
        quantity = action.get("quantity")

        # Validate SKU exists
        if sku:
            product = self.db.products.find_one({"sku": sku})
            if not product:
                errors.append(f"Product with SKU '{sku}' not found")

        # Validate warehouse exists and is active
        if warehouse_id:
            warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
            if not warehouse:
                errors.append(f"Warehouse '{warehouse_id}' not found")
            elif not warehouse.get("is_active", True):
                errors.append(f"Warehouse '{warehouse_id}' is not active")
            else:
                # Check capacity
                capacity = warehouse.get("capacity", 1)
                current = warehouse.get("current_utilization", 0)
                available_capacity = capacity - current

                if quantity and quantity > available_capacity:
                    warnings.append(
                        f"Warehouse near capacity. Adding {quantity} may exceed limits"
                    )

        # Validate quantity
        if quantity is not None:
            if quantity <= 0:
                errors.append("Quantity must be positive")
            elif quantity > 10000:
                warnings.append("Large quantity - verify this is intentional")

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.REPLENISH_INVENTORY,
            errors=errors,
            warnings=warnings
        )

    def _validate_transfer(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate transfer_inventory action"""
        errors = []
        warnings = []

        sku = action.get("sku")
        source_wh = action.get("source_warehouse")
        target_wh = action.get("target_warehouse")
        quantity = action.get("quantity")

        # Validate source and target are different
        if source_wh and target_wh and source_wh == target_wh:
            errors.append("Source and target warehouses must be different")

        # Validate source warehouse
        if source_wh:
            source = self.db.warehouses.find_one({"warehouse_id": source_wh})
            if not source:
                errors.append(f"Source warehouse '{source_wh}' not found")
            elif not source.get("is_active", True):
                errors.append(f"Source warehouse '{source_wh}' is not active")

        # Validate target warehouse
        if target_wh:
            target = self.db.warehouses.find_one({"warehouse_id": target_wh})
            if not target:
                errors.append(f"Target warehouse '{target_wh}' not found")
            elif not target.get("is_active", True):
                errors.append(f"Target warehouse '{target_wh}' is not active")

        # Validate stock availability at source
        if sku and source_wh and quantity:
            inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": source_wh
            })

            if not inv:
                errors.append(f"No inventory for SKU '{sku}' at warehouse '{source_wh}'")
            else:
                available = inv.get("current_stock", 0) - inv.get("reserved_stock", 0)
                if available < quantity:
                    errors.append(
                        f"Insufficient stock at source. Available: {available}, Requested: {quantity}"
                    )

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.TRANSFER_INVENTORY,
            errors=errors,
            warnings=warnings
        )

    def _validate_reroute(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate reroute_delivery action"""
        errors = []
        warnings = []

        delivery_id = action.get("delivery_id")
        new_warehouse = action.get("new_warehouse_id")

        # Validate delivery exists
        if delivery_id:
            delivery = self.db.deliveries.find_one({"delivery_id": delivery_id})
            if not delivery:
                errors.append(f"Delivery '{delivery_id}' not found")
            elif delivery.get("status") == "delivered":
                errors.append(f"Delivery '{delivery_id}' already delivered - cannot reroute")
            elif delivery.get("status") == "cancelled":
                errors.append(f"Delivery '{delivery_id}' is cancelled - cannot reroute")

        # Validate new warehouse if specified
        if new_warehouse:
            warehouse = self.db.warehouses.find_one({"warehouse_id": new_warehouse})
            if not warehouse:
                errors.append(f"New warehouse '{new_warehouse}' not found")
            elif not warehouse.get("is_active", True):
                errors.append(f"New warehouse '{new_warehouse}' is not active")

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.REROUTE_DELIVERY,
            errors=errors,
            warnings=warnings
        )

    def _validate_priority_change(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate change_delivery_priority action"""
        errors = []
        warnings = []

        delivery_id = action.get("delivery_id")
        new_priority = action.get("new_priority")

        valid_priorities = ["critical", "high", "normal", "low"]
        if new_priority and new_priority not in valid_priorities:
            errors.append(f"Invalid priority '{new_priority}'. Must be one of: {valid_priorities}")

        if delivery_id:
            delivery = self.db.deliveries.find_one({"delivery_id": delivery_id})
            if not delivery:
                errors.append(f"Delivery '{delivery_id}' not found")
            elif delivery.get("status") in ["delivered", "cancelled"]:
                errors.append(f"Cannot change priority - delivery is {delivery.get('status')}")

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.CHANGE_DELIVERY_PRIORITY,
            errors=errors,
            warnings=warnings
        )

    def _validate_reassign(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate reassign_warehouse action"""
        errors = []
        warnings = []

        order_id = action.get("order_id")
        new_warehouse = action.get("new_warehouse_id")

        if order_id:
            order = self.db.orders.find_one({"order_id": order_id})
            if not order:
                errors.append(f"Order '{order_id}' not found")
            elif order.get("status") in ["shipped", "delivered", "cancelled"]:
                errors.append(f"Cannot reassign - order is {order.get('status')}")

        if new_warehouse:
            warehouse = self.db.warehouses.find_one({"warehouse_id": new_warehouse})
            if not warehouse:
                errors.append(f"Warehouse '{new_warehouse}' not found")
            elif not warehouse.get("is_active", True):
                errors.append(f"Warehouse '{new_warehouse}' is not active")

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.REASSIGN_WAREHOUSE,
            errors=errors,
            warnings=warnings
        )

    def _validate_rebalance(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate rebalance_inventory action (uses transfer validation)"""
        return self._validate_transfer(action)

    def _validate_escalate(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate escalate_alert action"""
        errors = []
        warnings = []

        signal_id = action.get("signal_id")

        if signal_id:
            signal = self.db.signals.find_one({"signal_id": signal_id})
            if not signal:
                warnings.append(f"Signal '{signal_id}' not found - escalation may proceed anyway")

        return ValidationResult(
            valid=len(errors) == 0,
            action_id=action.get("action_id"),
            action_type=ActionType.ESCALATE_ALERT,
            errors=errors,
            warnings=warnings
        )

    def _validate_no_action(self, action: Dict[str, Any]) -> ValidationResult:
        """Validate no_action (always valid)"""
        return ValidationResult(
            valid=True,
            action_id=action.get("action_id"),
            action_type=ActionType.NO_ACTION,
            errors=[],
            warnings=[]
        )

    def can_auto_execute(self, validation_results: List[ValidationResult]) -> Tuple[bool, str]:
        """
        Determine if actions can be auto-executed.

        Args:
            validation_results: List of validation results

        Returns:
            Tuple of (can_execute, reason)
        """
        # Check for any errors
        for result in validation_results:
            if not result.valid:
                return False, f"Action {result.action_id} failed validation: {result.errors}"

        # Check for high-risk actions
        for result in validation_results:
            if result.action_type in [
                ActionType.TRANSFER_INVENTORY,
                ActionType.REASSIGN_WAREHOUSE
            ]:
                if result.warnings:
                    return False, f"Action {result.action_id} has warnings - requires review"

        return True, "All actions validated successfully"

    def get_safe_version(self, action: Dict[str, Any], validation_result: ValidationResult) -> Optional[Dict[str, Any]]:
        """
        Attempt to create a safe version of an action with corrections.

        Args:
            action: Original action
            validation_result: Validation result with errors

        Returns:
            Corrected action or None if cannot be corrected
        """
        # This could implement logic to fix common issues
        # For now, return None to indicate manual review needed
        return None


# Global instance
validation_service = ValidationService()
