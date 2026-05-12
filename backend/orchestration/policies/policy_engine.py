"""
Policy Engine

Validates and enforces governance rules for orchestration actions.
Prevents dangerous or unauthorized automation.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from orchestration.models.schemas import (
    Workflow, WorkflowPriority, ActionType
)
import logging

logger = logging.getLogger(__name__)


class PolicyRule:
    """Represents a single policy rule"""

    def __init__(
        self,
        name: str,
        description: str,
        condition: callable,
        action: str,  # "allow", "require_approval", "deny"
        severity: str = "medium"
    ):
        self.name = name
        self.description = description
        self.condition = condition
        self.action = action
        self.severity = severity


class PolicyEngine:
    """
    Validates orchestration actions against business policies.

    Ensures safe and compliant autonomous operations.
    """

    def __init__(self):
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> List[PolicyRule]:
        """Initialize default policy rules"""
        return [
            # QUANTITY RULES
            PolicyRule(
                name="max_transfer_quantity",
                description="Transfers above 500 units require approval",
                condition=lambda ctx: ctx.get("quantity", 0) <= 500,
                action="require_approval",
                severity="high"
            ),
            PolicyRule(
                name="max_emergency_order",
                description="Emergency orders above 1000 units require approval",
                condition=lambda ctx: not (
                    ctx.get("action_type") == ActionType.SUPPLIER_ORDER and
                    ctx.get("quantity", 0) > 1000
                ),
                action="require_approval",
                severity="high"
            ),

            # WAREHOUSE RULES
            PolicyRule(
                name="warehouse_utilization_limit",
                description="Cannot transfer to over-utilized warehouses (>95%)",
                condition=lambda ctx: ctx.get("target_utilization", 0) < 95,
                action="deny",
                severity="critical"
            ),
            PolicyRule(
                name="prevent_single_warehouse_drain",
                description="Cannot reduce warehouse stock below 10%",
                condition=lambda ctx: ctx.get("remaining_stock_pct", 100) > 10,
                action="deny",
                severity="critical"
            ),

            # COST RULES
            PolicyRule(
                name="max_order_cost",
                description="Orders above $100,000 require approval",
                condition=lambda ctx: ctx.get("estimated_cost", 0) <= 100000,
                action="require_approval",
                severity="high"
            ),

            # TIMING RULES
            PolicyRule(
                name="avoid_off_hours_critical",
                description="Critical operations outside business hours need approval",
                condition=lambda ctx: self._is_business_hours() or ctx.get("priority") != "critical",
                action="require_approval",
                severity="medium"
            ),

            # CONFLICT PREVENTION
            PolicyRule(
                name="prevent_concurrent_transfers",
                description="Cannot have multiple concurrent transfers for same SKU",
                condition=lambda ctx: not ctx.get("has_concurrent_transfer", False),
                action="deny",
                severity="high"
            ),

            # SUPPLIER RULES
            PolicyRule(
                name="preferred_suppliers_only",
                description="Auto-orders must use preferred suppliers",
                condition=lambda ctx: ctx.get("is_preferred_supplier", True),
                action="require_approval",
                severity="medium"
            ),

            # SAFETY STOCK RULES
            PolicyRule(
                name="maintain_safety_stock",
                description="Cannot reduce stock below safety level",
                condition=lambda ctx: ctx.get("remaining_stock", 0) >= ctx.get("safety_stock", 0),
                action="deny",
                severity="critical"
            )
        ]

    def validate_action(
        self,
        action_type: ActionType,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, str, str]:
        """
        Validate an action against all policies.

        Args:
            action_type: Type of action to validate
            parameters: Action parameters
            context: Execution context

        Returns:
            Tuple of (allowed, decision, reason)
            - allowed: True if action can proceed
            - decision: "allow", "require_approval", or "deny"
            - reason: Explanation
        """
        validation_context = {
            "action_type": action_type,
            **parameters,
            **context
        }

        violations = []
        requires_approval = []

        for rule in self.rules:
            try:
                passes = rule.condition(validation_context)

                if not passes:
                    if rule.action == "deny":
                        violations.append({
                            "rule": rule.name,
                            "description": rule.description,
                            "severity": rule.severity
                        })
                    elif rule.action == "require_approval":
                        requires_approval.append({
                            "rule": rule.name,
                            "description": rule.description,
                            "severity": rule.severity
                        })

            except Exception as e:
                logger.warning(f"Error evaluating rule {rule.name}: {e}")

        # Decision logic
        if violations:
            reason = "; ".join([v["description"] for v in violations])
            logger.warning(f"Action denied by policy: {reason}")
            return False, "deny", reason

        if requires_approval:
            reason = "; ".join([r["description"] for r in requires_approval])
            logger.info(f"Action requires approval: {reason}")
            return True, "require_approval", reason

        return True, "allow", "All policies passed"

    def validate_workflow(self, workflow: Workflow) -> Tuple[bool, str, List[str]]:
        """
        Validate all steps in a workflow.

        Args:
            workflow: Workflow to validate

        Returns:
            Tuple of (valid, decision, issues)
        """
        issues = []
        requires_approval = False

        for step in workflow.steps:
            allowed, decision, reason = self.validate_action(
                step.action_type,
                step.parameters,
                workflow.context_summary
            )

            if not allowed:
                issues.append(f"Step {step.step_id}: {reason}")
            elif decision == "require_approval":
                requires_approval = True
                issues.append(f"Step {step.step_id} requires approval: {reason}")

        if issues and not requires_approval:
            return False, "deny", issues

        if requires_approval:
            return True, "require_approval", issues

        return True, "allow", []

    def check_transfer_safety(
        self,
        sku: str,
        from_warehouse: str,
        to_warehouse: str,
        quantity: int,
        inventory_service
    ) -> Tuple[bool, str]:
        """
        Check if a stock transfer is safe to execute.

        Args:
            sku: Product SKU
            from_warehouse: Source warehouse
            to_warehouse: Destination warehouse
            quantity: Quantity to transfer
            inventory_service: Inventory service instance

        Returns:
            Tuple of (safe, reason)
        """
        try:
            # Check source has enough stock
            source_inv = inventory_service.get_inventory(sku, from_warehouse)
            if not source_inv or len(source_inv) == 0:
                return False, f"No inventory found for {sku} at {from_warehouse}"

            source_stock = source_inv[0].get("quantity", 0)
            source_reserved = source_inv[0].get("reserved_stock", 0)
            source_available = source_stock - source_reserved

            if source_available < quantity:
                return False, f"Insufficient stock at {from_warehouse}. Available: {source_available}, Requested: {quantity}"

            # Check destination is not over-utilized
            from services.warehouse_service import WarehouseService
            wh_service = WarehouseService()

            dest_wh = wh_service.db.warehouses.find_one({"warehouse_id": to_warehouse})
            if dest_wh:
                capacity = dest_wh.get("capacity", 0)
                current = dest_wh.get("current_utilization", 0)
                utilization_pct = (current / capacity * 100) if capacity > 0 else 0

                if utilization_pct > 95:
                    return False, f"Destination warehouse {to_warehouse} is over-utilized ({utilization_pct:.1f}%)"

            # Check we're not draining source completely
            remaining_pct = ((source_available - quantity) / source_stock * 100) if source_stock > 0 else 0
            if remaining_pct < 10:
                return False, f"Cannot drain source warehouse below 10% (would leave {remaining_pct:.1f}%)"

            return True, "Transfer is safe"

        except Exception as e:
            logger.error(f"Error checking transfer safety: {e}")
            return False, f"Error validating transfer: {str(e)}"

    def _is_business_hours(self) -> bool:
        """Check if current time is during business hours (9 AM - 6 PM)"""
        now = datetime.utcnow()
        return 9 <= now.hour < 18 and now.weekday() < 5  # Mon-Fri

    def add_custom_rule(self, rule: PolicyRule):
        """Add a custom policy rule"""
        self.rules.append(rule)
        logger.info(f"Added custom policy rule: {rule.name}")

    def get_policy_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all active policies"""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "action": rule.action,
                "severity": rule.severity
            }
            for rule in self.rules
        ]


# Global instance
policy_engine = PolicyEngine()
