"""
Workflow State Machine

Manages workflow transitions with validation and logging.
"""
from typing import Optional, Dict, Any, Set
from datetime import datetime
from orchestration.models.schemas import WorkflowStatus
import logging

logger = logging.getLogger(__name__)


class WorkflowStateMachine:
    """
    State machine for managing workflow lifecycle transitions.

    Validates transitions and maintains state integrity.
    """

    # Define allowed transitions: {from_state: {to_state: reason_required}}
    ALLOWED_TRANSITIONS: Dict[WorkflowStatus, Set[WorkflowStatus]] = {
        WorkflowStatus.CREATED: {
            WorkflowStatus.ANALYZING,
            WorkflowStatus.CANCELLED
        },
        WorkflowStatus.ANALYZING: {
            WorkflowStatus.PLANNING,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED
        },
        WorkflowStatus.PLANNING: {
            WorkflowStatus.WAITING_APPROVAL,
            WorkflowStatus.EXECUTING,  # If no approval needed
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED
        },
        WorkflowStatus.WAITING_APPROVAL: {
            WorkflowStatus.EXECUTING,  # When approved
            WorkflowStatus.CANCELLED   # When rejected
        },
        WorkflowStatus.EXECUTING: {
            WorkflowStatus.MONITORING,
            WorkflowStatus.FAILED,
            WorkflowStatus.ROLLED_BACK
        },
        WorkflowStatus.MONITORING: {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.ROLLED_BACK
        },
        WorkflowStatus.FAILED: {
            WorkflowStatus.EXECUTING,  # Retry
            WorkflowStatus.ROLLED_BACK,
            WorkflowStatus.COMPLETED  # Partial completion
        },
        WorkflowStatus.ROLLED_BACK: {
            WorkflowStatus.COMPLETED  # After recovery
        },
        WorkflowStatus.COMPLETED: set(),  # Terminal state
        WorkflowStatus.CANCELLED: set()   # Terminal state
    }

    def __init__(self):
        self.transition_history: Dict[str, list] = {}

    def can_transition(
        self,
        current_state: WorkflowStatus,
        target_state: WorkflowStatus
    ) -> bool:
        """
        Check if transition from current to target state is allowed.

        Args:
            current_state: Current workflow state
            target_state: Target workflow state

        Returns:
            True if transition is allowed
        """
        allowed_targets = self.ALLOWED_TRANSITIONS.get(current_state, set())
        return target_state in allowed_targets

    def transition(
        self,
        workflow_id: str,
        current_state: WorkflowStatus,
        target_state: WorkflowStatus,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a state transition with validation and logging.

        Args:
            workflow_id: Workflow identifier
            current_state: Current state
            target_state: Target state
            reason: Reason for transition
            metadata: Additional metadata

        Returns:
            Transition result with success status

        Raises:
            ValueError: If transition is not allowed
        """
        if not self.can_transition(current_state, target_state):
            error_msg = f"Invalid transition from {current_state} to {target_state} for workflow {workflow_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Record transition
        transition_record = {
            "from_state": current_state.value,
            "to_state": target_state.value,
            "reason": reason,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add to history
        if workflow_id not in self.transition_history:
            self.transition_history[workflow_id] = []
        self.transition_history[workflow_id].append(transition_record)

        logger.info(
            f"Workflow {workflow_id} transitioned: {current_state} -> {target_state}. "
            f"Reason: {reason}"
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "previous_state": current_state.value,
            "new_state": target_state.value,
            "transitioned_at": datetime.utcnow().isoformat()
        }

    def get_valid_next_states(self, current_state: WorkflowStatus) -> Set[WorkflowStatus]:
        """
        Get all valid next states from current state.

        Args:
            current_state: Current workflow state

        Returns:
            Set of valid next states
        """
        return self.ALLOWED_TRANSITIONS.get(current_state, set())

    def get_transition_history(self, workflow_id: str) -> list:
        """
        Get transition history for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of transition records
        """
        return self.transition_history.get(workflow_id, [])

    def is_terminal_state(self, state: WorkflowStatus) -> bool:
        """
        Check if state is terminal (no further transitions).

        Args:
            state: Workflow state

        Returns:
            True if state is terminal
        """
        return len(self.ALLOWED_TRANSITIONS.get(state, set())) == 0

    def get_state_duration_estimate(self, state: WorkflowStatus) -> int:
        """
        Get estimated duration in seconds for a state.

        Args:
            state: Workflow state

        Returns:
            Estimated duration in seconds
        """
        estimates = {
            WorkflowStatus.CREATED: 0,
            WorkflowStatus.ANALYZING: 30,
            WorkflowStatus.PLANNING: 60,
            WorkflowStatus.WAITING_APPROVAL: 3600,  # 1 hour average
            WorkflowStatus.EXECUTING: 300,
            WorkflowStatus.MONITORING: 600,
            WorkflowStatus.COMPLETED: 0,
            WorkflowStatus.FAILED: 0,
            WorkflowStatus.ROLLED_BACK: 300,
            WorkflowStatus.CANCELLED: 0
        }
        return estimates.get(state, 0)


class WorkflowStatusValidator:
    """Validates workflow status requirements"""

    @staticmethod
    def can_execute(status: WorkflowStatus) -> bool:
        """Check if workflow can be executed"""
        return status in {
            WorkflowStatus.PLANNING,
            WorkflowStatus.WAITING_APPROVAL,
            WorkflowStatus.EXECUTING
        }

    @staticmethod
    def requires_approval(status: WorkflowStatus) -> bool:
        """Check if workflow requires approval"""
        return status == WorkflowStatus.WAITING_APPROVAL

    @staticmethod
    def can_retry(status: WorkflowStatus) -> bool:
        """Check if workflow can be retried"""
        return status == WorkflowStatus.FAILED

    @staticmethod
    def can_rollback(status: WorkflowStatus) -> bool:
        """Check if workflow can be rolled back"""
        return status in {
            WorkflowStatus.EXECUTING,
            WorkflowStatus.MONITORING,
            WorkflowStatus.FAILED
        }

    @staticmethod
    def is_active(status: WorkflowStatus) -> bool:
        """Check if workflow is currently active"""
        return status in {
            WorkflowStatus.CREATED,
            WorkflowStatus.ANALYZING,
            WorkflowStatus.PLANNING,
            WorkflowStatus.WAITING_APPROVAL,
            WorkflowStatus.EXECUTING,
            WorkflowStatus.MONITORING
        }

    @staticmethod
    def is_complete(status: WorkflowStatus) -> bool:
        """Check if workflow has completed (successfully or not)"""
        return status in {
            WorkflowStatus.COMPLETED,
            WorkflowStatus.CANCELLED,
            WorkflowStatus.ROLLED_BACK
        }


# Global state machine instance
workflow_state_machine = WorkflowStateMachine()
workflow_status_validator = WorkflowStatusValidator()
