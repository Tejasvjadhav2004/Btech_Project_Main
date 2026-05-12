"""
Action Schema - Pydantic schemas for LLM orchestration actions

Defines structured outputs for all orchestration decisions.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """Allowed action types for orchestration"""
    REPLENISH_INVENTORY = "replenish_inventory"
    TRANSFER_INVENTORY = "transfer_inventory"
    REROUTE_DELIVERY = "reroute_delivery"
    CHANGE_DELIVERY_PRIORITY = "change_delivery_priority"
    REASSIGN_WAREHOUSE = "reassign_warehouse"
    REBALANCE_INVENTORY = "rebalance_inventory"
    ESCALATE_ALERT = "escalate_alert"
    PRIORITIZE_ORDERS = "prioritize_orders"
    ADJUST_REORDER_THRESHOLD = "adjust_reorder_threshold"
    NO_ACTION = "no_action"


class Priority(str, Enum):
    """Action priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionSchema(BaseModel):
    """Schema for a single orchestration action"""
    action_type: ActionType = Field(..., description="Type of action to execute")
    priority: Priority = Field(default=Priority.MEDIUM, description="Action priority")
    sku: Optional[str] = Field(None, description="Product SKU if applicable")
    source_warehouse: Optional[str] = Field(None, description="Source warehouse ID")
    target_warehouse: Optional[str] = Field(None, description="Target warehouse ID")
    store_id: Optional[str] = Field(None, description="Store ID if applicable")
    delivery_id: Optional[str] = Field(None, description="Delivery ID if applicable")
    order_id: Optional[str] = Field(None, description="Order ID if applicable")
    quantity: Optional[int] = Field(None, ge=1, description="Quantity for inventory actions")
    new_priority: Optional[str] = Field(None, description="New priority level")
    reason: Optional[str] = Field(None, description="Reason for action")

    @validator('quantity')
    def validate_quantity(cls, v, values):
        """Validate quantity for inventory actions"""
        action_type = values.get('action_type')
        if action_type in [
            ActionType.REPLENISH_INVENTORY,
            ActionType.TRANSFER_INVENTORY,
            ActionType.REBALANCE_INVENTORY
        ]:
            if v is None or v <= 0:
                raise ValueError(f"Quantity required for {action_type}")
        return v

    @validator('source_warehouse')
    def validate_source_warehouse(cls, v, values):
        """Validate source warehouse for transfer actions"""
        action_type = values.get('action_type')
        if action_type in [ActionType.TRANSFER_INVENTORY, ActionType.REBALANCE_INVENTORY]:
            if not v:
                raise ValueError(f"source_warehouse required for {action_type}")
        return v

    @validator('target_warehouse')
    def validate_target_warehouse(cls, v, values):
        """Validate target warehouse for transfer actions"""
        action_type = values.get('action_type')
        if action_type in [ActionType.TRANSFER_INVENTORY, ActionType.REBALANCE_INVENTORY]:
            if not v:
                raise ValueError(f"target_warehouse required for {action_type}")
        return v

    class Config:
        use_enum_values = True


class ReasoningItem(BaseModel):
    """Single reasoning step"""
    step: str = Field(..., description="Reasoning step description")
    data_point: Optional[str] = Field(None, description="Supporting data point")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence level")


class OrchestrationPlan(BaseModel):
    """Structured orchestration plan from LLM"""
    plan_id: str = Field(..., description="Unique plan identifier")
    priority: Priority = Field(..., description="Overall plan priority")
    situation: str = Field(..., description="Current situation summary")
    severity: str = Field(default="medium", description="Situation severity")
    actions: List[ActionSchema] = Field(default_factory=list, description="Actions to execute")
    reasoning: List[str] = Field(default_factory=list, description="Decision reasoning steps")
    expected_outcome: Optional[str] = Field(None, description="Expected outcome")
    risk_assessment: Optional[str] = Field(None, description="Risk assessment")
    alternative_actions: Optional[List[ActionSchema]] = Field(None, description="Alternative actions if primary fails")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class WorkflowSchema(BaseModel):
    """Schema for orchestration workflow"""
    workflow_id: str = Field(..., description="Unique workflow ID")
    plan_id: str = Field(..., description="Parent plan ID")
    status: Literal["pending", "validating", "executing", "completed", "failed", "rolled_back"] = "pending"
    actions: List[ActionSchema] = Field(default_factory=list)
    executed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    failed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    validation_results: Optional[Dict[str, Any]] = None
    execution_results: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class DecisionSchema(BaseModel):
    """Schema for orchestration decision with full context"""
    decision_id: str = Field(..., description="Unique decision ID")
    decision_type: str = Field(..., description="Type of decision")
    context: Dict[str, Any] = Field(..., description="Aggregated context that led to decision")
    plan: OrchestrationPlan = Field(..., description="Generated orchestration plan")
    confidence: float = Field(..., ge=0, le=1, description="Decision confidence")
    auto_execute: bool = Field(default=False, description="Whether to auto-execute")
    requires_approval: bool = Field(default=False, description="Whether approval needed")
    approval_role: Optional[str] = Field(None, description="Required approval role")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class ValidationResult(BaseModel):
    """Result of action validation"""
    valid: bool = Field(..., description="Whether action is valid")
    action_id: str = Field(..., description="Action identifier")
    action_type: ActionType = Field(..., description="Action type")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    corrected_action: Optional[ActionSchema] = Field(None, description="Corrected action if applicable")

    class Config:
        use_enum_values = True


class ExecutionResult(BaseModel):
    """Result of action execution"""
    success: bool = Field(..., description="Whether execution succeeded")
    action_id: str = Field(..., description="Action identifier")
    action_type: ActionType = Field(..., description="Action type")
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result details")
    error: Optional[str] = Field(None, description="Error message if failed")
    rollback_data: Optional[Dict[str, Any]] = Field(None, description="Data for rollback")

    class Config:
        use_enum_values = True


class OrchestrationHistory(BaseModel):
    """Schema for orchestration history entry"""
    history_id: str = Field(..., description="Unique history ID")
    decision_id: str = Field(..., description="Associated decision ID")
    plan_id: str = Field(..., description="Associated plan ID")
    context_summary: Dict[str, Any] = Field(..., description="Summarized context")
    decision: DecisionSchema = Field(..., description="The decision made")
    validation_results: List[ValidationResult] = Field(default_factory=list)
    execution_results: List[ExecutionResult] = Field(default_factory=list)
    status: str = Field(default="pending")
    reasoning: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class LLMResponse(BaseModel):
    """Raw LLM response wrapper"""
    raw_response: str = Field(..., description="Raw LLM text response")
    parsed_plan: Optional[OrchestrationPlan] = Field(None, description="Parsed plan")
    parse_success: bool = Field(default=False, description="Whether parsing succeeded")
    parse_errors: List[str] = Field(default_factory=list, description="Parsing errors")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage stats")
    model: Optional[str] = Field(None, description="Model used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
