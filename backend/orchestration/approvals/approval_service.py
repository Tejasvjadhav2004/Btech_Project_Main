"""
Approval Service

Manages approval workflows for orchestration actions that require human oversight.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from orchestration.models.schemas import (
    ApprovalRequest, ApprovalDecision, ApprovalStatus,
    Workflow, WorkflowPriority, WorkflowType
)
from orchestration.models.collections import get_approvals_collection
from orchestration.utils.helpers import generate_approval_id
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Manages approval requests for orchestration workflows.

    Handles approval routing, expiration, escalation, and decisions.
    """

    # Default approval expiry times by priority
    EXPIRY_HOURS = {
        WorkflowPriority.CRITICAL: 1,   # 1 hour
        WorkflowPriority.HIGH: 4,       # 4 hours
        WorkflowPriority.MEDIUM: 24,    # 24 hours
        WorkflowPriority.LOW: 48        # 48 hours
    }

    # Required roles by risk level
    ROLE_BY_RISK = {
        "low": "operations_manager",
        "medium": "operations_manager",
        "high": "supply_chain_director",
        "critical": "ceo"
    }

    def __init__(self):
        pass

    @property
    def db(self):
        return mongodb.get_database()

    def create_approval_request(
        self,
        workflow: Workflow,
        risk_level: str,
        impact_description: str,
        estimated_cost: Optional[float] = None
    ) -> ApprovalRequest:
        """
        Create an approval request for a workflow.

        Args:
            workflow: Workflow requiring approval
            risk_level: Risk level (low, medium, high, critical)
            impact_description: Description of business impact
            estimated_cost: Optional estimated cost of workflow

        Returns:
            Created approval request
        """
        approval_id = generate_approval_id()

        # Determine required role
        required_role = self.ROLE_BY_RISK.get(risk_level, "operations_manager")

        # Calculate expiry time
        expiry_hours = self.EXPIRY_HOURS.get(workflow.priority, 24)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

        # Create approval request
        approval = ApprovalRequest(
            approval_id=approval_id,
            workflow_id=workflow.workflow_id,
            workflow_type=workflow.workflow_type,
            priority=workflow.priority,
            action_summary=self._generate_action_summary(workflow),
            risk_level=risk_level,
            impact_description=impact_description,
            estimated_cost=estimated_cost,
            required_role=required_role,
            expires_at=expires_at
        )

        # Save to database
        self._save_approval(approval)

        logger.info(f"Created approval request {approval_id} for workflow {workflow.workflow_id}")
        return approval

    def process_approval_decision(self, decision: ApprovalDecision) -> Dict[str, Any]:
        """
        Process an approval decision.

        Args:
            decision: Approval decision with approve/reject

        Returns:
            Updated approval status
        """
        approval = self.get_approval(decision.approval_id)
        if not approval:
            raise ValueError(f"Approval {decision.approval_id} not found")

        # Check if already processed
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval already {approval.status}")

        # Check if expired
        if approval.expires_at and datetime.utcnow() > approval.expires_at:
            approval.status = ApprovalStatus.EXPIRED
            self._update_approval(approval)
            raise ValueError("Approval has expired")

        # Update based on decision
        if decision.decision == "approve":
            approval.status = ApprovalStatus.APPROVED
            approval.approved_by = decision.approved_by
            approval.approved_at = datetime.utcnow()

            self._log_approval_event(
                approval.approval_id,
                "approved",
                f"Approved by {decision.approved_by}",
                {"notes": decision.notes}
            )

        else:  # reject
            approval.status = ApprovalStatus.REJECTED
            approval.rejection_reason = decision.notes

            self._log_approval_event(
                approval.approval_id,
                "rejected",
                f"Rejected by {decision.approved_by}",
                {"reason": decision.notes}
            )

        self._update_approval(approval)

        logger.info(f"Approval {decision.approval_id} {decision.decision}d by {decision.approved_by}")

        return {
            "approval_id": approval.approval_id,
            "status": approval.status.value,
            "workflow_id": approval.workflow_id,
            "decision": decision.decision
        }

    def get_pending_approvals(
        self,
        required_role: Optional[str] = None,
        limit: int = 50
    ) -> List[ApprovalRequest]:
        """
        Get pending approval requests.

        Args:
            required_role: Filter by required role
            limit: Maximum results

        Returns:
            List of pending approvals
        """
        collection = get_approvals_collection()

        query = {"status": ApprovalStatus.PENDING.value}
        if required_role:
            query["required_role"] = required_role

        docs = collection.find(query).sort("created_at", 1).limit(limit)

        return [ApprovalRequest(**doc) for doc in docs]

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get approval by ID"""
        collection = get_approvals_collection()
        doc = collection.find_one({"approval_id": approval_id})
        if doc:
            return ApprovalRequest(**doc)
        return None

    def get_approval_for_workflow(self, workflow_id: str) -> Optional[ApprovalRequest]:
        """Get approval for a specific workflow"""
        collection = get_approvals_collection()
        doc = collection.find_one(
            {"workflow_id": workflow_id},
            sort=[("created_at", -1)]
        )
        if doc:
            return ApprovalRequest(**doc)
        return None

    def check_approval_expired(self, approval_id: str) -> bool:
        """Check if an approval has expired"""
        approval = self.get_approval(approval_id)
        if not approval:
            return True

        if approval.status != ApprovalStatus.PENDING:
            return False

        if approval.expires_at and datetime.utcnow() > approval.expires_at:
            # Mark as expired
            approval.status = ApprovalStatus.EXPIRED
            self._update_approval(approval)
            return True

        return False

    def escalate_approval(
        self,
        approval_id: str,
        escalate_to_role: str = "supply_chain_director"
    ) -> Dict[str, Any]:
        """
        Escalate an approval to higher authority.

        Args:
            approval_id: Approval to escalate
            escalate_to_role: Role to escalate to

        Returns:
            Escalated approval details
        """
        approval = self.get_approval(approval_id)
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")

        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Cannot escalate approval in {approval.status} status")

        # Update role
        old_role = approval.required_role
        approval.required_role = escalate_to_role
        approval.escalation_count += 1
        approval.escalated_to = escalate_to_role

        self._update_approval(approval)

        self._log_approval_event(
            approval_id,
            "escalated",
            f"Escalated from {old_role} to {escalate_to_role}",
            {}
        )

        logger.info(f"Approval {approval_id} escalated to {escalate_to_role}")

        return {
            "approval_id": approval_id,
            "status": approval.status.value,
            "new_role": escalate_to_role,
            "escalation_count": approval.escalation_count
        }

    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        collection = get_approvals_collection()

        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_approval_time": {
                        "$avg": {
                            "$cond": [
                                {"$eq": ["$status", "approved"]},
                                {"$subtract": ["$approved_at", "$created_at"]},
                                None
                            ]
                        }
                    }
                }
            }
        ]

        results = list(collection.aggregate(pipeline))

        stats = {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
            "escalated": 0,
            "avg_approval_time_hours": 0
        }

        for result in results:
            status = result["_id"]
            stats[status] = result["count"]

        return stats

    def _generate_action_summary(self, workflow: Workflow) -> str:
        """Generate human-readable action summary"""
        step_count = len(workflow.steps)
        action_types = list(set(step.action_type.value for step in workflow.steps))

        return f"Workflow {workflow.workflow_type.value} with {step_count} steps: {', '.join(action_types)}"

    def _save_approval(self, approval: ApprovalRequest):
        """Save approval to database"""
        collection = get_approvals_collection()
        approval_dict = approval.dict()
        collection.insert_one(approval_dict)

    def _update_approval(self, approval: ApprovalRequest):
        """Update approval in database"""
        collection = get_approvals_collection()
        collection.update_one(
            {"approval_id": approval.approval_id},
            {"$set": approval.dict()}
        )

    def _log_approval_event(
        self,
        approval_id: str,
        event_type: str,
        message: str,
        details: Dict[str, Any]
    ):
        """Log approval event"""
        try:
            from orchestration.models.collections import get_workflow_logs_collection
            from orchestration.utils.helpers import generate_log_id

            collection = get_workflow_logs_collection()
            log_entry = {
                "log_id": generate_log_id(),
                "workflow_id": f"approval-{approval_id}",
                "event_type": f"approval_{event_type}",
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            collection.insert_one(log_entry)
        except Exception as e:
            logger.error(f"Failed to log approval event: {e}")


# Global instance
approval_service = ApprovalService()
