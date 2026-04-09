"""
Signal Service - Signal management for Sensing & Intelligence Layer

Handles creation, updates, duplicate prevention, and lifecycle management of signals.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
from api.config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class SignalType:
    """Signal type constants"""
    LOW_STOCK = "LOW_STOCK"
    STOCKOUT = "STOCKOUT"
    OVERSTOCK = "OVERSTOCK"
    DEMAND_SPIKE = "DEMAND_SPIKE"
    DEMAND_DROP = "DEMAND_DROP"
    DELIVERY_DELAY = "DELIVERY_DELAY"
    OVER_UTILIZATION = "OVER_UTILIZATION"
    UNDER_UTILIZATION = "UNDER_UTILIZATION"


class SignalSeverity:
    """Signal severity constants"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalStatus:
    """Signal status constants"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class SignalService:
    """Service for signal management"""
    
    COLLECTION_NAME = "signals"
    EVENT_LOGS_COLLECTION = "event_logs"
    
    # Severity rules based on signal type and conditions
    SEVERITY_RULES = {
        SignalType.STOCKOUT: SignalSeverity.CRITICAL,
        SignalType.LOW_STOCK: {
            "critical_threshold": 5,
            "high_threshold": 10,
            "default": SignalSeverity.MEDIUM
        },
        SignalType.OVERSTOCK: SignalSeverity.LOW,
        SignalType.DEMAND_SPIKE: SignalSeverity.HIGH,
        SignalType.DEMAND_DROP: SignalSeverity.MEDIUM,
        SignalType.DELIVERY_DELAY: {
            "critical_hours": 72,
            "high_hours": 48,
            "default": SignalSeverity.MEDIUM
        },
        SignalType.OVER_UTILIZATION: {
            "critical_threshold": 95,
            "default": SignalSeverity.HIGH
        },
        SignalType.UNDER_UTILIZATION: SignalSeverity.LOW
    }
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def _generate_signal_id(self) -> str:
        """Generate unique signal ID"""
        return f"SIG-{uuid.uuid4().hex[:8].upper()}"
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"EVT-{uuid.uuid4().hex[:8].upper()}"
    
    def _determine_severity(
        self, 
        signal_type: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Determine signal severity based on type and conditions.
        
        Rules:
        - STOCKOUT: Always CRITICAL
        - LOW_STOCK: CRITICAL if stock < 5, HIGH if < 10, else MEDIUM
        - DELIVERY_DELAY: CRITICAL if > 72h, HIGH if > 48h, else MEDIUM
        - OVER_UTILIZATION: CRITICAL if > 95%, else HIGH
        - OVERSTOCK, UNDER_UTILIZATION: LOW
        - DEMAND_SPIKE: HIGH
        - DEMAND_DROP: MEDIUM
        """
        rule = self.SEVERITY_RULES.get(signal_type)
        
        if rule is None:
            return SignalSeverity.MEDIUM
        
        if isinstance(rule, str):
            return rule
        
        # Complex rules based on details
        if signal_type == SignalType.LOW_STOCK and details:
            current_stock = details.get("current_stock", 0)
            if current_stock <= rule.get("critical_threshold", 5):
                return SignalSeverity.CRITICAL
            elif current_stock <= rule.get("high_threshold", 10):
                return SignalSeverity.HIGH
        
        elif signal_type == SignalType.DELIVERY_DELAY and details:
            delay_hours = details.get("delay_hours", 0)
            if delay_hours >= rule.get("critical_hours", 72):
                return SignalSeverity.CRITICAL
            elif delay_hours >= rule.get("high_hours", 48):
                return SignalSeverity.HIGH
        
        elif signal_type == SignalType.OVER_UTILIZATION and details:
            utilization = details.get("utilization_percent", 0)
            if utilization >= rule.get("critical_threshold", 95):
                return SignalSeverity.CRITICAL
        
        return rule.get("default", SignalSeverity.MEDIUM)
    
    def _generate_message(
        self, 
        signal_type: str, 
        entity_type: str, 
        entity_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable message for the signal"""
        
        messages = {
            SignalType.LOW_STOCK: lambda: f"Low stock alert for {details.get('product_name', details.get('sku', 'product'))} at {entity_type} {entity_id}. Current: {details.get('current_stock', 'N/A')}, Threshold: {details.get('threshold', 'N/A')}",
            
            SignalType.STOCKOUT: lambda: f"STOCKOUT: {details.get('product_name', details.get('sku', 'product'))} is out of stock at {entity_type} {entity_id}",
            
            SignalType.OVERSTOCK: lambda: f"Overstock detected for {details.get('product_name', details.get('sku', 'product'))} at {entity_type} {entity_id}. Current: {details.get('current_stock', 'N/A')}, Normal: {details.get('normal_stock', 'N/A')}",
            
            SignalType.DEMAND_SPIKE: lambda: f"Demand spike detected: {details.get('current_orders', 'N/A')} orders vs {details.get('average_orders', 'N/A')} average ({details.get('spike_factor', 'N/A')}x increase)",
            
            SignalType.DEMAND_DROP: lambda: f"Demand drop detected: {details.get('current_orders', 'N/A')} orders vs {details.get('average_orders', 'N/A')} average ({details.get('drop_factor', 'N/A')}x decrease)",
            
            SignalType.DELIVERY_DELAY: lambda: f"Delivery {entity_id} is delayed by {details.get('delay_hours', 'N/A')} hours. Expected: {details.get('expected_arrival', 'N/A')}",
            
            SignalType.OVER_UTILIZATION: lambda: f"Warehouse {entity_id} is over-utilized at {details.get('utilization_percent', 'N/A')}% (threshold: {details.get('threshold', 90)}%)",
            
            SignalType.UNDER_UTILIZATION: lambda: f"Warehouse {entity_id} is under-utilized at {details.get('utilization_percent', 'N/A')}% (threshold: {details.get('threshold', 20)}%)"
        }
        
        message_func = messages.get(signal_type)
        if message_func:
            try:
                return message_func()
            except Exception:
                pass
        
        return f"{signal_type} signal for {entity_type} {entity_id}"
    
    def check_duplicate_signal(
        self,
        signal_type: str,
        entity_type: str,
        entity_id: str,
        product_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if an active signal already exists for this entity/type combination.
        
        Returns the existing signal if found, None otherwise.
        """
        query = {
            "type": signal_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "status": SignalStatus.ACTIVE
        }
        
        if product_id:
            query["product_id"] = product_id
        else:
            query["product_id"] = {"$exists": False}
        
        return self.db[self.COLLECTION_NAME].find_one(query)
    
    def create_signal(
        self,
        signal_type: str,
        entity_type: str,
        entity_id: str,
        product_id: Optional[str] = None,
        severity: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        threshold: Optional[Dict[str, Any]] = None,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        Create a new signal with duplicate prevention.
        
        If an active signal already exists for this entity/type/product,
        returns the existing signal instead of creating a duplicate.
        
        Args:
            signal_type: Type of signal (use SignalType constants)
            entity_type: Type of entity (warehouse, store, delivery, product)
            entity_id: ID of the entity
            product_id: Optional product ID (for inventory signals)
            severity: Optional severity override (auto-determined if not provided)
            message: Optional message override (auto-generated if not provided)
            details: Additional context details
            threshold: Threshold values that triggered the signal
            source: Source of the signal (scheduler, event_trigger, manual)
        
        Returns:
            Created or existing signal document
        """
        try:
            # Check for duplicate
            existing = self.check_duplicate_signal(
                signal_type, entity_type, entity_id, product_id
            )
            
            if existing:
                logger.debug(
                    f"Duplicate signal exists: {existing['signal_id']} "
                    f"for {signal_type} on {entity_type}/{entity_id}"
                )
                # Update the existing signal's details if they've changed
                if details and details != existing.get("details"):
                    self.db[self.COLLECTION_NAME].update_one(
                        {"signal_id": existing["signal_id"]},
                        {
                            "$set": {
                                "details": details,
                                "updated_at": datetime.utcnow()
                            }
                        }
                    )
                return existing
            
            # Determine severity if not provided
            if severity is None:
                severity = self._determine_severity(signal_type, details)
            
            # Generate message if not provided
            if message is None:
                message = self._generate_message(
                    signal_type, entity_type, entity_id, details
                )
            
            # Generate signal ID
            signal_id = self._generate_signal_id()
            
            # Create signal document
            signal = {
                "signal_id": signal_id,
                "type": signal_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "severity": severity,
                "status": SignalStatus.ACTIVE,
                "message": message,
                "details": details or {},
                "threshold": threshold or {},
                "created_at": datetime.utcnow(),
                "acknowledged_at": None,
                "resolved_at": None,
                "auto_resolved": False,
                "action_taken": None,
                "updated_at": datetime.utcnow()
            }
            
            if product_id:
                signal["product_id"] = product_id
            
            # Insert signal
            result = self.db[self.COLLECTION_NAME].insert_one(signal)
            signal["_id"] = result.inserted_id
            
            # Log event
            self._log_event(
                signal_id=signal_id,
                event_type="signal_created",
                action=None,
                status="success",
                source=source,
                metadata={
                    "type": signal_type,
                    "severity": severity,
                    "entity_type": entity_type,
                    "entity_id": entity_id
                }
            )
            
            logger.info(
                f"Created signal {signal_id}: {signal_type} ({severity}) "
                f"for {entity_type}/{entity_id}"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error creating signal: {e}")
            raise
    
    def acknowledge_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """
        Acknowledge a signal (mark as seen but not resolved).
        """
        result = self.db[self.COLLECTION_NAME].update_one(
            {"signal_id": signal_id, "status": SignalStatus.ACTIVE},
            {
                "$set": {
                    "status": SignalStatus.ACKNOWLEDGED,
                    "acknowledged_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            self._log_event(
                signal_id=signal_id,
                event_type="signal_acknowledged",
                status="success",
                source="manual"
            )
            logger.info(f"Acknowledged signal {signal_id}")
            return self.get_signal(signal_id)
        
        return None
    
    def resolve_signal(
        self,
        signal_id: str,
        auto_resolved: bool = False,
        action_taken: Optional[Dict[str, Any]] = None,
        resolution_note: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a signal.
        
        Args:
            signal_id: Signal ID to resolve
            auto_resolved: Whether resolved automatically by the system
            action_taken: Details of action taken to resolve
            resolution_note: Optional note about resolution
        """
        update_data = {
            "status": SignalStatus.RESOLVED,
            "resolved_at": datetime.utcnow(),
            "auto_resolved": auto_resolved,
            "updated_at": datetime.utcnow()
        }
        
        if action_taken:
            update_data["action_taken"] = action_taken
        
        if resolution_note:
            update_data["resolution_note"] = resolution_note
        
        result = self.db[self.COLLECTION_NAME].update_one(
            {
                "signal_id": signal_id,
                "status": {"$in": [SignalStatus.ACTIVE, SignalStatus.ACKNOWLEDGED]}
            },
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            self._log_event(
                signal_id=signal_id,
                event_type="signal_resolved",
                status="success",
                source="system" if auto_resolved else "manual",
                metadata={"auto_resolved": auto_resolved, "action_taken": action_taken}
            )
            logger.info(f"Resolved signal {signal_id} (auto={auto_resolved})")
            return self.get_signal(signal_id)
        
        return None
    
    def expire_stale_signals(self, hours: int = None) -> int:
        """
        Expire signals that have been active beyond the threshold.
        
        Returns the number of signals expired.
        """
        if hours is None:
            hours = settings.signal_auto_resolve_hours
        
        threshold_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = self.db[self.COLLECTION_NAME].update_many(
            {
                "status": SignalStatus.ACTIVE,
                "created_at": {"$lt": threshold_time}
            },
            {
                "$set": {
                    "status": SignalStatus.EXPIRED,
                    "resolved_at": datetime.utcnow(),
                    "auto_resolved": True,
                    "resolution_note": f"Auto-expired after {hours} hours",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Expired {result.modified_count} stale signals")
        
        return result.modified_count
    
    def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get a signal by ID"""
        signal = self.db[self.COLLECTION_NAME].find_one({"signal_id": signal_id})
        if signal:
            signal["id"] = str(signal.pop("_id"))
        return signal
    
    def get_active_signals(
        self,
        signal_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get active signals with optional filters"""
        query = {"status": SignalStatus.ACTIVE}
        
        if signal_type:
            query["type"] = signal_type
        if entity_type:
            query["entity_type"] = entity_type
        if entity_id:
            query["entity_id"] = entity_id
        if severity:
            query["severity"] = severity
        
        signals = list(self.db[self.COLLECTION_NAME].find(query).sort(
            [("severity", -1), ("created_at", -1)]
        ).limit(limit))
        
        for signal in signals:
            signal["id"] = str(signal.pop("_id"))
        
        return signals
    
    def get_signals(
        self,
        status: Optional[str] = None,
        signal_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get signals with optional filters"""
        query = {}
        
        if status:
            query["status"] = status
        if signal_type:
            query["type"] = signal_type
        if entity_type:
            query["entity_type"] = entity_type
        if severity:
            query["severity"] = severity
        if since:
            query["created_at"] = {"$gte": since}
        
        signals = list(self.db[self.COLLECTION_NAME].find(query).sort(
            "created_at", -1
        ).limit(limit))
        
        for signal in signals:
            signal["id"] = str(signal.pop("_id"))
        
        return signals
    
    def get_signal_stats(self) -> Dict[str, Any]:
        """Get signal statistics"""
        pipeline = [
            {
                "$facet": {
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_type": [
                        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
                    ],
                    "by_severity": [
                        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
                    ],
                    "by_entity_type": [
                        {"$group": {"_id": "$entity_type", "count": {"$sum": 1}}}
                    ],
                    "total": [
                        {"$count": "count"}
                    ],
                    "recent_24h": [
                        {
                            "$match": {
                                "created_at": {
                                    "$gte": datetime.utcnow() - timedelta(hours=24)
                                }
                            }
                        },
                        {"$count": "count"}
                    ]
                }
            }
        ]
        
        result = list(self.db[self.COLLECTION_NAME].aggregate(pipeline))
        
        if not result:
            return {
                "total_signals": 0,
                "active_signals": 0,
                "resolved_signals": 0,
                "by_type": {},
                "by_severity": {},
                "by_entity_type": {},
                "recent_24h": 0
            }
        
        data = result[0]
        
        stats = {
            "total_signals": data["total"][0]["count"] if data["total"] else 0,
            "active_signals": 0,
            "resolved_signals": 0,
            "by_status": {},
            "by_type": {},
            "by_severity": {},
            "by_entity_type": {},
            "recent_24h": data["recent_24h"][0]["count"] if data["recent_24h"] else 0
        }
        
        for item in data["by_status"]:
            stats["by_status"][item["_id"]] = item["count"]
            if item["_id"] == SignalStatus.ACTIVE:
                stats["active_signals"] = item["count"]
            elif item["_id"] == SignalStatus.RESOLVED:
                stats["resolved_signals"] = item["count"]
        
        for item in data["by_type"]:
            stats["by_type"][item["_id"]] = item["count"]
        
        for item in data["by_severity"]:
            stats["by_severity"][item["_id"]] = item["count"]
        
        for item in data["by_entity_type"]:
            stats["by_entity_type"][item["_id"]] = item["count"]
        
        return stats
    
    def _log_event(
        self,
        signal_id: Optional[str] = None,
        event_type: str = "signal_created",
        action: Optional[str] = None,
        status: str = "success",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ):
        """Log an event to the event_logs collection"""
        try:
            event = {
                "event_id": self._generate_event_id(),
                "signal_id": signal_id,
                "event_type": event_type,
                "action": action,
                "status": status,
                "source": source,
                "metadata": metadata or {},
                "error": error,
                "timestamp": datetime.utcnow()
            }
            
            self.db[self.EVENT_LOGS_COLLECTION].insert_one(event)
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    def get_event_logs(
        self,
        signal_id: Optional[str] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get event logs with optional filters"""
        query = {}
        
        if signal_id:
            query["signal_id"] = signal_id
        if event_type:
            query["event_type"] = event_type
        if source:
            query["source"] = source
        if since:
            query["timestamp"] = {"$gte": since}
        
        events = list(self.db[self.EVENT_LOGS_COLLECTION].find(query).sort(
            "timestamp", -1
        ).limit(limit))
        
        for event in events:
            event["id"] = str(event.pop("_id"))
        
        return events


# Global signal service instance
signal_service = SignalService()
