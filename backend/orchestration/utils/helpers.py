"""
Orchestration Utilities

Common utilities for workflow management, ID generation, and helpers.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


def generate_workflow_id() -> str:
    """Generate unique workflow ID"""
    return f"WF-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_step_id() -> str:
    """Generate unique step ID"""
    return f"STEP-{uuid.uuid4().hex[:8].upper()}"


def generate_approval_id() -> str:
    """Generate unique approval ID"""
    return f"APR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def generate_action_id() -> str:
    """Generate unique action ID"""
    return f"ACT-{uuid.uuid4().hex[:8].upper()}"


def generate_log_id() -> str:
    """Generate unique log ID"""
    return f"LOG-{uuid.uuid4().hex[:8].upper()}"


def calculate_execution_time(start: datetime, end: datetime) -> float:
    """Calculate execution time in seconds"""
    return (end - start).total_seconds()


def is_workflow_expired(created_at: datetime, expiry_hours: int = 24) -> bool:
    """Check if workflow has expired"""
    expiry_time = created_at + timedelta(hours=expiry_hours)
    return datetime.utcnow() > expiry_time


def prioritize_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort steps by priority and dependencies.
    Topological sort based on dependencies.
    """
    # Build dependency graph
    in_degree = {step['step_id']: 0 for step in steps}
    graph = {step['step_id']: [] for step in steps}

    for step in steps:
        for dep in step.get('dependencies', []):
            if dep in graph:
                graph[dep].append(step['step_id'])
                in_degree[step['step_id']] += 1

    # Kahn's algorithm for topological sort
    queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
    sorted_steps = []

    while queue:
        current = queue.pop(0)
        sorted_steps.append(current)

        for neighbor in graph.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Map back to step objects
    step_map = {step['step_id']: step for step in steps}
    return [step_map[step_id] for step_id in sorted_steps if step_id in step_map]


def estimate_workflow_risk(context: Dict[str, Any]) -> str:
    """
    Estimate risk level for workflow based on context.
    Returns: 'low', 'medium', 'high'
    """
    risk_score = 0

    # High severity signals
    if context.get('signal_severity') == 'critical':
        risk_score += 3
    elif context.get('signal_severity') == 'high':
        risk_score += 2

    # Low stock levels - handle None values
    available_stock = context.get('available_stock') or 0
    if available_stock < 10:
        risk_score += 2

    # High warehouse utilization - handle None values
    warehouse_utilization = context.get('warehouse_utilization') or 0
    if warehouse_utilization > 90:
        risk_score += 1

    # High predicted demand - handle None values
    predicted_demand = context.get('predicted_demand') or 0
    if predicted_demand > 100:
        risk_score += 1

    # Delivery delays - handle None values
    delay_risk = context.get('delay_risk') or 0
    if delay_risk > 0.7:
        risk_score += 1

    if risk_score >= 5:
        return 'high'
    elif risk_score >= 3:
        return 'medium'
    else:
        return 'low'


def calculate_timeout_duration(priority: str) -> timedelta:
    """
    Calculate workflow timeout based on priority.
    """
    timeouts = {
        'critical': timedelta(minutes=30),
        'high': timedelta(hours=1),
        'medium': timedelta(hours=4),
        'low': timedelta(hours=24)
    }
    return timeouts.get(priority, timedelta(hours=4))


class WorkflowTimer:
    """Context manager for timing workflow operations"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None

    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        return False
