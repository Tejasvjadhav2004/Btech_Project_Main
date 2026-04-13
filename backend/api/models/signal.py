"""
Signal Models - Pydantic models for Sensing & Intelligence Layer
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """Types of signals that can be generated"""
    LOW_STOCK = "LOW_STOCK"
    STOCKOUT = "STOCKOUT"
    OVERSTOCK = "OVERSTOCK"
    DEMAND_SPIKE = "DEMAND_SPIKE"
    DEMAND_DROP = "DEMAND_DROP"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    OVER_UTILIZATION = "OVER_UTILIZATION"
    UNDER_UTILIZATION = "UNDER_UTILIZATION"


class SignalSeverity(str, Enum):
    """Signal severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalStatus(str, Enum):
    """Signal status values"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class EntityType(str, Enum):
    """Types of entities that can generate signals"""
    WAREHOUSE = "warehouse"
    STORE = "store"
    DELIVERY = "delivery"
    PRODUCT = "product"
    ORDER = "order"


class EventType(str, Enum):
    """Types of events logged"""
    SIGNAL_CREATED = "signal_created"
    SIGNAL_ACKNOWLEDGED = "signal_acknowledged"
    SIGNAL_RESOLVED = "signal_resolved"
    ACTION_EXECUTED = "action_executed"
    DETECTION_RUN = "detection_run"
    SCHEDULER_TICK = "scheduler_tick"


class ActionType(str, Enum):
    """Types of automated actions"""
    CREATE_REPLENISHMENT_ORDER = "create_replenishment_order"
    SEND_ALERT = "send_alert"
    ESCALATE = "escalate"
    LOG_WARNING = "log_warning"
    ADJUST_THRESHOLD = "adjust_threshold"
    NO_ACTION = "no_action"


# Request/Response Models

class SignalCreate(BaseModel):
    """Model for creating a new signal"""
    type: SignalType
    entity_type: EntityType
    entity_id: str
    product_id: Optional[str] = None
    severity: Optional[SignalSeverity] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    threshold: Optional[Dict[str, Any]] = None


class SignalUpdate(BaseModel):
    """Model for updating a signal"""
    status: Optional[SignalStatus] = None
    severity: Optional[SignalSeverity] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SignalResponse(BaseModel):
    """Model for signal response"""
    signal_id: str
    type: SignalType
    entity_type: EntityType
    entity_id: str
    product_id: Optional[str] = None
    severity: SignalSeverity
    status: SignalStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    threshold: Optional[Dict[str, Any]] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    auto_resolved: bool = False
    action_taken: Optional[Dict[str, Any]] = None


class SignalListResponse(BaseModel):
    """Model for list of signals"""
    signals: List[SignalResponse]
    total: int
    active_count: int
    resolved_count: int


class EventLogCreate(BaseModel):
    """Model for creating an event log"""
    signal_id: Optional[str] = None
    event_type: EventType
    action: Optional[ActionType] = None
    status: str = "success"
    source: str = "manual"
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class EventLogResponse(BaseModel):
    """Model for event log response"""
    event_id: str
    signal_id: Optional[str] = None
    event_type: EventType
    action: Optional[ActionType] = None
    status: str
    source: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime


class SignalStats(BaseModel):
    """Model for signal statistics"""
    total_signals: int
    active_signals: int
    resolved_signals: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_entity_type: Dict[str, int]
    recent_24h: int


class DetectionResult(BaseModel):
    """Model for detection function results"""
    detection_type: str
    signals_generated: int
    items_checked: int
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class DecisionResult(BaseModel):
    """Model for decision engine results"""
    signal_id: str
    action_taken: ActionType
    success: bool
    message: str
    execution_details: Optional[Dict[str, Any]] = None
    timestamp: datetime
