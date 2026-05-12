"""
Orchestration Models and Schemas

Pydantic models for workflow management, approvals, and execution tracking.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow lifecycle states"""
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class WorkflowPriority(str, Enum):
    """Workflow priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkflowType(str, Enum):
    """Supported workflow types"""
    STOCKOUT_MITIGATION = "stockout_mitigation"
    INVENTORY_REBALANCE = "inventory_rebalance"
    OVERLOAD_BALANCING = "overload_balancing"
    DELAY_RECOVERY = "delay_recovery"
    EMERGENCY_REPLENISHMENT = "emergency_replenishment"
    DEMAND_SURGE_RESPONSE = "demand_surge_response"
    DELIVERY_REROUTING = "delivery_rerouting"
    WAREHOUSE_OPTIMIZATION = "warehouse_optimization"


class ApprovalStatus(str, Enum):
    """Approval states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"


class ExecutionStatus(str, Enum):
    """Action execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class ActionType(str, Enum):
    """Types of orchestration actions"""
    INVENTORY_TRANSFER = "inventory_transfer"
    CREATE_REPLENISHMENT_ORDER = "create_replenishment_order"
    DELIVERY_REROUTE = "delivery_reroute"
    WAREHOUSE_REASSIGNMENT = "warehouse_reassignment"
    PRIORITY_ADJUSTMENT = "priority_adjustment"
    STOCK_RESERVATION = "stock_reservation"
    SUPPLIER_ORDER = "supplier_order"
    DELIVERY_EXPEDITE = "delivery_expedite"
    INVENTORY_ADJUSTMENT = "inventory_adjustment"


# ============================================================
# CONTEXT MODELS
# ============================================================

class OperationalContext(BaseModel):
    """Aggregated operational context for orchestration"""
    signal_id: str
    signal_type: str
    signal_severity: str
    sku: Optional[str] = None
    warehouse_id: Optional[str] = None
    store_id: Optional[str] = None

    # Inventory context
    current_stock: Optional[int] = None
    available_stock: Optional[int] = None
    reserved_stock: Optional[int] = None

    # Warehouse context
    warehouse_utilization: Optional[float] = None
    warehouse_capacity: Optional[int] = None
    nearby_warehouses: List[Dict[str, Any]] = []

    # Prediction context
    predicted_demand: Optional[float] = None
    stockout_risk: Optional[float] = None
    delay_risk: Optional[float] = None

    # Order context
    pending_orders: Optional[int] = None
    priority_orders: Optional[int] = None

    # Delivery context
    active_deliveries: Optional[int] = None
    delayed_deliveries: Optional[int] = None

    # Timing
    lead_time_days: Optional[int] = None

    # Raw details
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# WORKFLOW MODELS
# ============================================================

class WorkflowStep(BaseModel):
    """Individual workflow step"""
    step_id: str
    action_type: ActionType
    description: str
    parameters: Dict[str, Any] = {}
    dependencies: List[str] = []  # step_ids that must complete first
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    rollback_data: Optional[Dict[str, Any]] = None


class Workflow(BaseModel):
    """Complete workflow definition"""
    workflow_id: str
    workflow_type: WorkflowType
    trigger_signal_id: str
    trigger_signal_type: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    priority: WorkflowPriority = WorkflowPriority.MEDIUM

    # Context reference
    context_summary: Dict[str, Any] = {}

    # Steps
    steps: List[WorkflowStep] = []
    current_step_index: int = 0

    # Approval
    requires_approval: bool = False
    approval_id: Optional[str] = None

    # Execution tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Performance metrics
    execution_time_seconds: Optional[float] = None

    # Recovery
    retry_count: int = 0
    max_retries: int = 3
    rollback_enabled: bool = True

    # Audit
    created_by: str = "system"
    triggered_reason: str = ""
    notes: List[str] = []


class WorkflowLog(BaseModel):
    """Workflow execution log"""
    log_id: str
    workflow_id: str
    step_id: Optional[str] = None
    event_type: str
    message: str
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# APPROVAL MODELS
# ============================================================

class ApprovalRequest(BaseModel):
    """Approval request for workflow"""
    approval_id: str
    workflow_id: str
    workflow_type: WorkflowType
    priority: WorkflowPriority

    # What needs approval
    action_summary: str
    risk_level: str  # low, medium, high
    impact_description: str
    estimated_cost: Optional[float] = None

    # Approval routing
    required_role: str = "operations_manager"
    assigned_to: Optional[str] = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING

    # Decision
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Escalation
    escalation_count: int = 0
    escalated_to: Optional[str] = None


class ApprovalDecision(BaseModel):
    """Approval decision input"""
    approval_id: str
    decision: Literal["approve", "reject"]
    approved_by: str
    notes: Optional[str] = None


# ============================================================
# EXECUTION MODELS
# ============================================================

class ActionResult(BaseModel):
    """Result of action execution"""
    action_id: str
    action_type: ActionType
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Results
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Rollback info
    can_rollback: bool = False
    rollback_data: Optional[Dict[str, Any]] = None

    # Service references
    service_used: Optional[str] = None
    service_response: Optional[Dict[str, Any]] = None


class ExecutionPlan(BaseModel):
    """Execution plan with prioritized actions"""
    plan_id: str
    workflow_id: str
    actions: List[Dict[str, Any]]  # Ordered list of actions
    estimated_duration_seconds: Optional[float] = None
    estimated_cost: Optional[float] = None
    risk_assessment: Optional[Dict[str, Any]] = None


# ============================================================
# MONITORING MODELS
# ============================================================

class WorkflowMetrics(BaseModel):
    """Workflow performance metrics"""
    total_workflows: int = 0
    active_workflows: int = 0
    completed_workflows: int = 0
    failed_workflows: int = 0
    rolled_back_workflows: int = 0

    avg_execution_time_seconds: Optional[float] = None
    success_rate: Optional[float] = None

    # Approval metrics
    pending_approvals: int = 0
    avg_approval_time_seconds: Optional[float] = None
    approval_rate: Optional[float] = None

    # Action metrics
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    retry_count: int = 0


class OrchestrationHealth(BaseModel):
    """Health status of orchestration layer"""
    status: str = "healthy"
    orchestrator_active: bool = True
    active_workflows: int = 0
    pending_approvals: int = 0
    failed_workflows_last_hour: int = 0
    last_workflow_timestamp: Optional[datetime] = None
    services_available: Dict[str, bool] = {}
    issues: List[str] = []
