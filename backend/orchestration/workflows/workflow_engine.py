"""
Workflow Engine

Generates and manages multi-step orchestration workflows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from orchestration.models.schemas import (
    Workflow, WorkflowStep, WorkflowStatus, WorkflowPriority,
    WorkflowType, ActionType, OperationalContext
)
from orchestration.state_machine.workflow_state_machine import (
    workflow_state_machine, WorkflowStatusValidator
)
from orchestration.utils.helpers import (
    generate_workflow_id, generate_step_id, estimate_workflow_risk
)
from orchestration.models.collections import get_workflows_collection, get_workflow_logs_collection
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Plans, creates, and manages orchestration workflows.

    Generates multi-step action plans based on signal context.
    """

    # Workflow type to signal type mapping
    SIGNAL_WORKFLOW_MAP = {
        "LOW_STOCK": WorkflowType.STOCKOUT_MITIGATION,
        "STOCKOUT": WorkflowType.EMERGENCY_REPLENISHMENT,
        "PREDICTED_STOCKOUT": WorkflowType.STOCKOUT_MITIGATION,
        "OVER_UTILIZATION": WorkflowType.OVERLOAD_BALANCING,
        "UNDER_UTILIZATION": WorkflowType.INVENTORY_REBALANCE,
        "DELIVERY_DELAY": WorkflowType.DELAY_RECOVERY,
        "PREDICTED_DELAY": WorkflowType.DELAY_RECOVERY,
        "DEMAND_SPIKE": WorkflowType.DEMAND_SURGE_RESPONSE,
        "PREDICTED_OVER_UTILIZATION": WorkflowType.OVERLOAD_BALANCING
    }

    def __init__(self):
        pass

    @property
    def db(self):
        return mongodb.get_database()

    def create_workflow(
        self,
        signal: Dict[str, Any],
        context: OperationalContext,
        priority: Optional[WorkflowPriority] = None
    ) -> Workflow:
        """
        Create a new workflow based on signal and context.

        Args:
            signal: Triggering signal
            context: Aggregated operational context
            priority: Optional priority override

        Returns:
            Created workflow document
        """
        signal_type = signal.get("type")
        signal_id = signal.get("signal_id")

        # Determine workflow type
        workflow_type = self.SIGNAL_WORKFLOW_MAP.get(
            signal_type,
            WorkflowType.STOCKOUT_MITIGATION
        )

        # Determine priority
        if not priority:
            severity = signal.get("severity", "medium")
            priority_map = {
                "critical": WorkflowPriority.CRITICAL,
                "high": WorkflowPriority.HIGH,
                "medium": WorkflowPriority.MEDIUM,
                "low": WorkflowPriority.LOW
            }
            priority = priority_map.get(severity, WorkflowPriority.MEDIUM)

        # Generate workflow ID
        workflow_id = generate_workflow_id()

        # Create workflow object
        workflow = Workflow(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            trigger_signal_id=signal_id,
            trigger_signal_type=signal_type,
            status=WorkflowStatus.CREATED,
            priority=priority,
            context_summary=self._summarize_context(context),
            created_by="orchestration_engine",
            triggered_reason=f"Signal {signal_type} triggered workflow"
        )

        # Persist workflow
        self._save_workflow(workflow)

        # Log creation
        self._log_workflow_event(
            workflow_id,
            "workflow_created",
            f"Workflow created for signal {signal_id}",
            {"signal_type": signal_type, "priority": priority.value}
        )

        logger.info(f"Created workflow {workflow_id} for signal {signal_id}")
        return workflow

    def plan_workflow(
        self,
        workflow: Workflow,
        context: OperationalContext
    ) -> Workflow:
        """
        Plan workflow steps based on context and workflow type.

        Args:
            workflow: Workflow document
            context: Operational context

        Returns:
            Updated workflow with planned steps
        """
        workflow_id = workflow.workflow_id

        # Transition to ANALYZING
        self._transition_workflow(workflow, WorkflowStatus.ANALYZING)

        # Generate steps based on workflow type
        steps = self._generate_workflow_steps(workflow, context)

        # Sort steps by dependencies
        steps = self._topological_sort_steps(steps)

        # Update workflow
        workflow.steps = steps
        workflow.status = WorkflowStatus.PLANNING
        workflow.updated_at = datetime.utcnow()

        # Check if approval needed
        risk_level = estimate_workflow_risk(context.dict())
        workflow.requires_approval = self._check_approval_required(workflow, risk_level)

        # Save updated workflow
        self._update_workflow(workflow)

        self._log_workflow_event(
            workflow_id,
            "workflow_planned",
            f"Workflow planned with {len(steps)} steps",
            {"steps_count": len(steps), "requires_approval": workflow.requires_approval}
        )

        logger.info(f"Planned workflow {workflow_id}: {len(steps)} steps")
        return workflow

    def _generate_workflow_steps(
        self,
        workflow: Workflow,
        context: OperationalContext
    ) -> List[WorkflowStep]:
        """
        Generate workflow steps based on workflow type and context.
        """
        workflow_type = workflow.workflow_type

        if workflow_type == WorkflowType.STOCKOUT_MITIGATION:
            return self._plan_stockout_mitigation(context)
        elif workflow_type == WorkflowType.EMERGENCY_REPLENISHMENT:
            return self._plan_emergency_replenishment(context)
        elif workflow_type == WorkflowType.INVENTORY_REBALANCE:
            return self._plan_inventory_rebalance(context)
        elif workflow_type == WorkflowType.OVERLOAD_BALANCING:
            return self._plan_overload_balancing(context)
        elif workflow_type == WorkflowType.DELAY_RECOVERY:
            return self._plan_delay_recovery(context)
        elif workflow_type == WorkflowType.DEMAND_SURGE_RESPONSE:
            return self._plan_demand_surge_response(context)
        else:
            return self._plan_default_workflow(context)

    def _plan_stockout_mitigation(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan stockout mitigation workflow"""
        steps = []

        # Step 1: Check nearby warehouses for stock transfer
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.INVENTORY_TRANSFER,
            description=f"Check and transfer stock from nearby warehouses for {context.sku}",
            parameters={
                "sku": context.sku,
                "target_location": context.warehouse_id or context.store_id,
                "quantity_needed": max(50, (context.predicted_demand or 50) - (context.available_stock or 0))
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Step 2: Create replenishment order if needed
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.CREATE_REPLENISHMENT_ORDER,
            description=f"Create replenishment order for {context.sku}",
            parameters={
                "sku": context.sku,
                "warehouse_id": context.warehouse_id,
                "quantity": context.predicted_demand or 100,
                "priority": "high"
            },
            dependencies=[step1.step_id],
            status="pending"
        )
        steps.append(step2)

        # Step 3: Adjust delivery priorities
        step3 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.PRIORITY_ADJUSTMENT,
            description="Reprioritize deliveries for affected orders",
            parameters={
                "sku": context.sku,
                "new_priority": "high"
            },
            dependencies=[step1.step_id],
            status="pending"
        )
        steps.append(step3)

        return steps

    def _plan_emergency_replenishment(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan emergency replenishment workflow"""
        steps = []

        # Immediate supplier order
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.SUPPLIER_ORDER,
            description=f"Emergency supplier order for {context.sku}",
            parameters={
                "sku": context.sku,
                "warehouse_id": context.warehouse_id,
                "quantity": 200,
                "priority": "critical",
                "expedite": True
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Expedite delivery
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.DELIVERY_EXPEDITE,
            description="Expedite incoming deliveries",
            parameters={
                "sku": context.sku,
                "expedite_all": True
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step2)

        return steps

    def _plan_inventory_rebalance(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan inventory rebalancing workflow"""
        steps = []

        # Find overstocked warehouses
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.INVENTORY_TRANSFER,
            description="Transfer stock from overstocked to understocked locations",
            parameters={
                "sku": context.sku,
                "source_criteria": "overstock",
                "target_criteria": "understock"
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Update reorder thresholds
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.INVENTORY_ADJUSTMENT,
            description="Update reorder thresholds based on demand",
            parameters={
                "sku": context.sku,
                "adjustment_type": "threshold_update"
            },
            dependencies=[step1.step_id],
            status="pending"
        )
        steps.append(step2)

        return steps

    def _plan_overload_balancing(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan warehouse overload balancing workflow"""
        steps = []

        # Identify alternative warehouses
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.WAREHOUSE_REASSIGNMENT,
            description="Reassign orders to less utilized warehouses",
            parameters={
                "current_warehouse": context.warehouse_id,
                "utilization_threshold": 80
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Reroute pending deliveries
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.DELIVERY_REROUTE,
            description="Reroute pending deliveries to alternate warehouses",
            parameters={
                "from_warehouse": context.warehouse_id,
                "reroute_criteria": "pending_only"
            },
            dependencies=[step1.step_id],
            status="pending"
        )
        steps.append(step2)

        return steps

    def _plan_delay_recovery(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan delivery delay recovery workflow"""
        steps = []

        # Reroute delayed deliveries
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.DELIVERY_REROUTE,
            description="Find alternate routes for delayed deliveries",
            parameters={
                "delivery_status": "in_transit",
                "delay_hours_threshold": 24
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Update customer expectations
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.PRIORITY_ADJUSTMENT,
            description="Adjust priorities for affected orders",
            parameters={
                "affected_deliveries": True
            },
            dependencies=[step1.step_id],
            status="pending"
        )
        steps.append(step2)

        return steps

    def _plan_demand_surge_response(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan demand surge response workflow"""
        steps = []

        # Create additional replenishment orders
        step1 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.CREATE_REPLENISHMENT_ORDER,
            description="Increase replenishment to meet surge",
            parameters={
                "sku": context.sku,
                "quantity_multiplier": 1.5,
                "priority": "high"
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step1)

        # Reserve stock for high-priority customers
        step2 = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.STOCK_RESERVATION,
            description="Reserve stock for priority orders",
            parameters={
                "sku": context.sku,
                "reserve_percentage": 30
            },
            dependencies=[],
            status="pending"
        )
        steps.append(step2)

        return steps

    def _plan_default_workflow(self, context: OperationalContext) -> List[WorkflowStep]:
        """Plan default workflow for unknown types"""
        steps = []

        step = WorkflowStep(
            step_id=generate_step_id(),
            action_type=ActionType.INVENTORY_ADJUSTMENT,
            description="Generic inventory adjustment",
            parameters={"sku": context.sku},
            dependencies=[],
            status="pending"
        )
        steps.append(step)

        return steps

    def _topological_sort_steps(self, steps: List[WorkflowStep]) -> List[WorkflowStep]:
        """Sort steps respecting dependencies"""
        # Build dependency graph
        in_degree = {step.step_id: 0 for step in steps}
        step_map = {step.step_id: step for step in steps}

        for step in steps:
            for dep in step.dependencies:
                if dep in in_degree:
                    in_degree[step.step_id] += 1

        # Kahn's algorithm
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        sorted_steps = []

        while queue:
            current = queue.pop(0)
            sorted_steps.append(step_map[current])

            for step in steps:
                if current in step.dependencies:
                    in_degree[step.step_id] -= 1
                    if in_degree[step.step_id] == 0:
                        queue.append(step.step_id)

        return sorted_steps

    def _check_approval_required(self, workflow: Workflow, risk_level: str) -> bool:
        """Check if workflow requires approval"""
        # Require approval for:
        # - High risk workflows
        # - Large quantity transfers (>500 units)
        # - Emergency supplier orders (>1000 units)
        # - Actions outside business hours for critical priority
        #
        # NOTE: Critical priority no longer auto-requires approval to enable
        # faster automated response to stockouts and critical signals.

        if risk_level == "high":
            return True

        # Check for large quantity actions
        for step in workflow.steps:
            qty = step.parameters.get("quantity") or 0
            if qty and qty > 500:
                return True

        # Check for emergency orders with large quantities
        for step in workflow.steps:
            if step.action_type == ActionType.SUPPLIER_ORDER:
                qty = step.parameters.get("quantity") or 0
                if qty and qty > 1000:
                    return True

        return False

    def _summarize_context(self, context: OperationalContext) -> Dict[str, Any]:
        """Create summary of context for workflow"""
        return {
            "signal_type": context.signal_type,
            "sku": context.sku,
            "warehouse_id": context.warehouse_id,
            "available_stock": context.available_stock,
            "predicted_demand": context.predicted_demand
        }

    def _transition_workflow(
        self,
        workflow: Workflow,
        target_status: WorkflowStatus,
        reason: str = ""
    ):
        """Transition workflow to new status"""
        workflow_state_machine.transition(
            workflow.workflow_id,
            workflow.status,
            target_status,
            reason
        )
        workflow.status = target_status
        workflow.updated_at = datetime.utcnow()

    def _save_workflow(self, workflow: Workflow):
        """Save workflow to database"""
        collection = get_workflows_collection()
        workflow_dict = workflow.dict()
        workflow_dict["created_at"] = datetime.utcnow()
        workflow_dict["updated_at"] = datetime.utcnow()
        collection.insert_one(workflow_dict)

    def _update_workflow(self, workflow: Workflow):
        """Update workflow in database"""
        collection = get_workflows_collection()
        workflow.updated_at = datetime.utcnow()
        collection.update_one(
            {"workflow_id": workflow.workflow_id},
            {"$set": workflow.dict()}
        )

    def _log_workflow_event(
        self,
        workflow_id: str,
        event_type: str,
        message: str,
        details: Dict[str, Any]
    ):
        """Log workflow event"""
        try:
            from orchestration.utils.helpers import generate_log_id
            collection = get_workflow_logs_collection()
            log_entry = {
                "log_id": generate_log_id(),
                "workflow_id": workflow_id,
                "event_type": event_type,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log workflow event: {e}")

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        collection = get_workflows_collection()
        doc = collection.find_one({"workflow_id": workflow_id})
        if doc:
            return Workflow(**doc)
        return None

    def get_active_workflows(self, limit: int = 100) -> List[Workflow]:
        """Get all active workflows"""
        collection = get_workflows_collection()
        active_statuses = [
            WorkflowStatus.CREATED,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.PLANNING,
            WorkflowStatus.WAITING_APPROVAL,
            WorkflowStatus.EXECUTING,
            WorkflowStatus.MONITORING
        ]

        docs = collection.find({
            "status": {"$in": [s.value for s in active_statuses]}
        }).sort("created_at", -1).limit(limit)

        return [Workflow(**doc) for doc in docs]


# Global instance
workflow_engine = WorkflowEngine()
