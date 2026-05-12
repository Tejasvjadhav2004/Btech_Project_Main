"""
Orchestrator Service - Central Orchestration Engine

Main entry point for all orchestration operations.
Coordinates context aggregation, workflow planning, policy validation,
approvals, execution, and recovery.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.connection import mongodb
from orchestration.models.schemas import (
    Workflow, WorkflowStatus, WorkflowPriority,
    ApprovalStatus, OperationalContext, WorkflowStep
)
from orchestration.context.context_service import context_service
from orchestration.workflows.workflow_engine import workflow_engine
from orchestration.state_machine.workflow_state_machine import (
    workflow_state_machine, WorkflowStatusValidator
)
from orchestration.policies.policy_engine import policy_engine
from orchestration.approvals.approval_service import approval_service
from orchestration.execution.execution_engine import execution_engine
from orchestration.models.collections import (
    setup_orchestration_collections, get_workflows_collection, get_workflow_logs_collection
)
from orchestration.utils.helpers import generate_log_id
import logging
import asyncio

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Central orchestration engine for autonomous supply chain management.

    Coordinates:
    - Signal processing and context aggregation
    - Workflow planning and execution
    - Policy validation and approvals
    - Failure recovery and rollback
    """

    def __init__(self):
        self._initialized = False
        self._active = False

    @property
    def db(self):
        return mongodb.get_database()

    def initialize(self):
        """Initialize orchestration layer"""
        if self._initialized:
            return

        # Setup collections
        setup_orchestration_collections()

        self._initialized = True
        logger.info("Orchestrator Service initialized")

    def start(self):
        """Start the orchestrator"""
        if not self._initialized:
            self.initialize()

        self._active = True
        logger.info("Orchestrator Service started")

    def stop(self):
        """Stop the orchestrator"""
        self._active = False
        logger.info("Orchestrator Service stopped")

    def is_active(self) -> bool:
        """Check if orchestrator is active"""
        return self._active

    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a signal through the complete orchestration pipeline.

        Flow:
        1. Aggregate context
        2. Create workflow
        3. Plan workflow
        4. Validate against policies
        5. Check approval requirements
        6. Execute or wait for approval
        7. Monitor and handle failures

        Args:
            signal: Signal document to process

        Returns:
            Orchestration result with workflow details
        """
        if not self._active:
            return {"success": False, "error": "Orchestrator not active"}

        signal_id = signal.get("signal_id")
        signal_type = signal.get("type")

        logger.info(f"Processing signal {signal_id} of type {signal_type}")

        try:
            # STEP 1: Aggregate context
            self._log_event(
                f"signal-{signal_id}",
                "context_aggregation_started",
                f"Aggregating context for {signal_type}"
            )

            context = context_service.aggregate_context_for_signal(signal)

            # STEP 2: Create workflow
            self._log_event(
                f"signal-{signal_id}",
                "workflow_creation_started",
                "Creating orchestration workflow"
            )

            workflow = workflow_engine.create_workflow(signal, context)

            # STEP 3: Plan workflow
            workflow = workflow_engine.plan_workflow(workflow, context)

            # STEP 4: Validate policies
            valid, decision, issues = policy_engine.validate_workflow(workflow)

            if not valid:
                workflow.status = WorkflowStatus.CANCELLED
                workflow_engine._update_workflow(workflow)

                return {
                    "success": False,
                    "workflow_id": workflow.workflow_id,
                    "reason": "Policy validation failed",
                    "issues": issues
                }

            # Check if approval needed
            if decision == "require_approval" or workflow.requires_approval:
                # STEP 5: Create approval request
                return await self._request_approval(workflow, context)

            # STEP 6: Execute immediately
            if decision == "allow":
                return await self._execute_workflow(workflow)

            return {
                "success": True,
                "workflow_id": workflow.workflow_id,
                "status": "planned",
                "decision": decision
            }

        except Exception as e:
            logger.error(f"Error processing signal {signal_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "signal_id": signal_id
            }

    async def _request_approval(
        self,
        workflow: Workflow,
        context: OperationalContext
    ) -> Dict[str, Any]:
        """Request approval for workflow"""
        from orchestration.utils.helpers import estimate_workflow_risk

        risk_level = estimate_workflow_risk(context.dict())

        approval = approval_service.create_approval_request(
            workflow=workflow,
            risk_level=risk_level,
            impact_description=f"Workflow for signal {workflow.trigger_signal_type}"
        )

        workflow.status = WorkflowStatus.WAITING_APPROVAL
        workflow.approval_id = approval.approval_id
        workflow_engine._update_workflow(workflow)

        self._log_event(
            workflow.workflow_id,
            "approval_requested",
            f"Approval {approval.approval_id} requested",
            {"approval_id": approval.approval_id, "risk_level": risk_level}
        )

        return {
            "success": True,
            "workflow_id": workflow.workflow_id,
            "status": "waiting_approval",
            "approval_id": approval.approval_id,
            "required_role": approval.required_role,
            "expires_at": approval.expires_at.isoformat() if approval.expires_at else None
        }

    async def _execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        """Execute workflow steps"""
        workflow_id = workflow.workflow_id

        # Transition to EXECUTING
        workflow_state_machine.transition(
            workflow_id,
            workflow.status,
            WorkflowStatus.EXECUTING,
            "Starting execution"
        )

        workflow.status = WorkflowStatus.EXECUTING
        workflow.started_at = datetime.utcnow()
        workflow_engine._update_workflow(workflow)

        self._log_event(
            workflow_id,
            "execution_started",
            f"Executing workflow with {len(workflow.steps)} steps"
        )

        executed_steps = []
        failed = False

        for step in workflow.steps:
            # Check dependencies
            if not self._check_dependencies(step, executed_steps):
                step.status = "skipped"
                workflow_engine._update_workflow(workflow)
                continue

            # Execute step
            result = await execution_engine.execute_step(workflow, step)
            executed_steps.append(step.step_id)

            if result.get("status") == "failed":
                failed = True

                # Handle failure
                recovery_result = await self._handle_step_failure(workflow, step, result)

                if not recovery_result.get("recovered"):
                    workflow.notes.append(f"Workflow failed at step {step.step_id}: {result.get('error')}")
                    break

            workflow_engine._update_workflow(workflow)

        # Determine final status
        if failed:
            workflow.status = WorkflowStatus.FAILED
        else:
            workflow.status = WorkflowStatus.MONITORING
            # Brief monitoring period (in production, would be async)
            workflow.status = WorkflowStatus.COMPLETED

        workflow.completed_at = datetime.utcnow()
        workflow.execution_time_seconds = (
            workflow.completed_at - workflow.started_at
        ).total_seconds() if workflow.started_at else 0

        workflow_engine._update_workflow(workflow)

        self._log_event(
            workflow_id,
            "execution_completed",
            f"Workflow completed with status {workflow.status}",
            {"execution_time_seconds": workflow.execution_time_seconds}
        )

        # Build result
        result = {
            "success": not failed,
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "steps_executed": len(executed_steps),
            "execution_time_seconds": workflow.execution_time_seconds
        }

        # Resolve signals after successful execution
        if not failed:
            try:
                resolved_signals = execution_engine.resolve_related_signals(workflow, result)
                result["resolved_signals"] = resolved_signals
                logger.info(f"Resolved {len(resolved_signals)} signals after workflow completion")
            except Exception as e:
                logger.warning(f"Failed to resolve signals: {e}")

        return result

    async def _handle_step_failure(
        self,
        workflow: Workflow,
        step: WorkflowStep,
        error_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle step execution failure.

        Strategies:
        1. Retry if retry_count < max_retries
        2. Try alternate action
        3. Rollback and fail

        Args:
            workflow: Parent workflow
            step: Failed step
            error_result: Error details

        Returns:
            Recovery result
        """
        logger.warning(f"Step {step.step_id} failed: {error_result.get('error')}")

        # Check retry count
        if step.retry_count < workflow.max_retries:
            step.retry_count += 1
            logger.info(f"Retrying step {step.step_id} (attempt {step.retry_count})")

            # Wait briefly before retry
            await asyncio.sleep(1)

            result = await execution_engine.execute_step(workflow, step)

            if result.get("status") == "success":
                return {"recovered": True, "method": "retry"}

        # Try rollback
        if workflow.rollback_enabled and step.rollback_data:
            logger.info(f"Attempting rollback for step {step.step_id}")
            rollback_result = await execution_engine.rollback_step(workflow, step)
            return {"recovered": False, "rollback": rollback_result}

        return {"recovered": False, "error": error_result.get("error")}

    def _check_dependencies(
        self,
        step: WorkflowStep,
        completed_steps: List[str]
    ) -> bool:
        """Check if step dependencies are met"""
        for dep in step.dependencies:
            if dep not in completed_steps:
                return False
        return True

    # ============================================================
    # PUBLIC API METHODS
    # ============================================================

    async def approve_workflow(
        self,
        workflow_id: str,
        approved_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a workflow and initiate execution.

        Args:
            workflow_id: Workflow to approve
            approved_by: User approving
            notes: Optional notes

        Returns:
            Approval and execution result
        """
        workflow = workflow_engine.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.approval_id:
            raise ValueError("Workflow has no approval request")

        # Process approval
        from orchestration.models.schemas import ApprovalDecision

        decision = ApprovalDecision(
            approval_id=workflow.approval_id,
            decision="approve",
            approved_by=approved_by,
            notes=notes
        )

        result = approval_service.process_approval_decision(decision)

        # Execute workflow
        execution_result = await self._execute_workflow(workflow)

        return {
            "approval": result,
            "execution": execution_result
        }

    async def reject_workflow(
        self,
        workflow_id: str,
        rejected_by: str,
        reason: str
    ) -> Dict[str, Any]:
        """Reject a workflow"""
        workflow = workflow_engine.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.approval_id:
            raise ValueError("Workflow has no approval request")

        from orchestration.models.schemas import ApprovalDecision

        decision = ApprovalDecision(
            approval_id=workflow.approval_id,
            decision="reject",
            approved_by=rejected_by,
            notes=reason
        )

        result = approval_service.process_approval_decision(decision)

        # Cancel workflow
        workflow.status = WorkflowStatus.CANCELLED
        workflow.notes.append(f"Rejected by {rejected_by}: {reason}")
        workflow_engine._update_workflow(workflow)

        return result

    async def get_active_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        workflows = workflow_engine.get_active_workflows(limit)
        return [w.dict() for w in workflows]

    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        workflow = workflow_engine.get_workflow(workflow_id)
        return workflow.dict() if workflow else None

    async def get_workflow_logs(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get logs for a workflow"""
        collection = get_workflow_logs_collection()
        logs = list(collection.find(
            {"workflow_id": workflow_id}
        ).sort("timestamp", -1).limit(100))

        for log in logs:
            log.pop("_id", None)

        return logs

    async def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics"""
        collection = get_workflows_collection()

        # Count by status
        pipeline = [
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]

        status_counts = {item["_id"]: item["count"] for item in collection.aggregate(pipeline)}

        # Calculate execution time
        completed = list(collection.find({
            "status": "completed",
            "execution_time_seconds": {"$exists": True}
        }).limit(100))

        avg_execution_time = 0
        if completed:
            avg_execution_time = sum(
                w.get("execution_time_seconds", 0) for w in completed
            ) / len(completed)

        # Get approval stats
        approval_stats = approval_service.get_approval_stats()

        return {
            "total_workflows": sum(status_counts.values()),
            "active_workflows": sum(
                status_counts.get(s.value, 0) for s in [
                    WorkflowStatus.CREATED,
                    WorkflowStatus.ANALYZING,
                    WorkflowStatus.PLANNING,
                    WorkflowStatus.EXECUTING,
                    WorkflowStatus.MONITORING
                ]
            ),
            "completed_workflows": status_counts.get("completed", 0),
            "failed_workflows": status_counts.get("failed", 0),
            "avg_execution_time_seconds": avg_execution_time,
            "approval_stats": approval_stats,
            "status_breakdown": status_counts
        }

    # ============================================================
    # EVENT-DRIVEN ORCHESTRATION
    # ============================================================

    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle orchestration events.

        Supported events:
        - signal_created: Trigger new workflow
        - prediction_generated: Check for risks
        - delivery_delayed: Trigger recovery
        - approval_received: Process approval
        - stockout_detected: Emergency response

        Args:
            event_type: Type of event
            event_data: Event payload

        Returns:
            Event handling result
        """
        logger.info(f"Handling event: {event_type}")

        if event_type == "signal_created":
            # Process signal through orchestration
            signal = event_data.get("signal")
            if signal:
                return await self.process_signal(signal)

        elif event_type == "approval_received":
            # Process approval decision
            approval_id = event_data.get("approval_id")
            decision = event_data.get("decision")
            approved_by = event_data.get("approved_by")

            if decision == "approve":
                approval = approval_service.get_approval(approval_id)
                if approval:
                    return await self.approve_workflow(
                        approval.workflow_id,
                        approved_by,
                        event_data.get("notes")
                    )

        elif event_type == "delivery_delayed":
            # Trigger delay recovery workflow
            signal = {
                "signal_id": f"delay-{datetime.utcnow().timestamp()}",
                "type": "DELIVERY_DELAY",
                "severity": "high",
                "details": event_data
            }
            return await self.process_signal(signal)

        elif event_type == "stockout_detected":
            # Trigger emergency replenishment
            signal = {
                "signal_id": f"stockout-{datetime.utcnow().timestamp()}",
                "type": "STOCKOUT",
                "severity": "critical",
                "details": event_data
            }
            return await self.process_signal(signal)

        return None

    def _log_event(
        self,
        workflow_id: str,
        event_type: str,
        message: str,
        details: Dict[str, Any] = None
    ):
        """Log orchestration event"""
        try:
            collection = get_workflow_logs_collection()
            log_entry = {
                "log_id": generate_log_id(),
                "workflow_id": workflow_id,
                "event_type": event_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log event: {e}")


# Global orchestrator instance
orchestrator_service = OrchestratorService()
