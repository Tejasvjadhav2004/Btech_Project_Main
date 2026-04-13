"""
Execution Logger Service - Track all decisions and execution steps
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from db.connection import mongodb
import logging
import uuid

logger = logging.getLogger(__name__)


class ExecutionLogLevel:
    """Log level constants"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class ExecutionStep:
    """Execution step constants"""
    ORDER_CREATED = "order_created"
    ORDER_VALIDATED = "order_validated"
    WAREHOUSE_SELECTED = "warehouse_selected"
    INVENTORY_ALLOCATED = "inventory_allocated"
    DELIVERY_CREATED = "delivery_created"
    ORDER_STATUS_UPDATED = "order_status_updated"
    DELIVERY_STATUS_UPDATED = "delivery_status_updated"
    ERROR = "error"


class ExecutionLogger:
    """Service for logging execution decisions and steps"""
    
    COLLECTION_NAME = "execution_logs"
    
    def __init__(self):
        self.db = mongodb.get_database()
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the execution_logs collection exists with proper indexes"""
        if self.db is not None:
            collection = self.db[self.COLLECTION_NAME]
            # Create indexes for common queries
            collection.create_index("order_id")
            collection.create_index("execution_id")
            collection.create_index("timestamp")
            collection.create_index("step")
    
    def create_execution(self, order_id: str) -> str:
        """
        Create a new execution tracking record.
        Returns execution_id for tracking all steps.
        """
        execution_id = f"EXE-{uuid.uuid4().hex[:8].upper()}"
        
        execution_record = {
            "execution_id": execution_id,
            "order_id": order_id,
            "status": "started",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "steps": [],
            "summary": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        self.db[self.COLLECTION_NAME].insert_one(execution_record)
        logger.info(f"Created execution {execution_id} for order {order_id}")
        
        return execution_id
    
    def log_step(
        self,
        execution_id: str,
        step: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = ExecutionLogLevel.INFO
    ) -> Dict[str, Any]:
        """
        Log an execution step.
        
        Args:
            execution_id: Execution tracking ID
            step: Step name (use ExecutionStep constants)
            message: Human-readable message
            details: Additional details/data
            level: Log level (info, warning, error, success)
        
        Returns:
            The logged step record
        """
        step_record = {
            "step_id": f"STEP-{uuid.uuid4().hex[:6].upper()}",
            "step": step,
            "message": message,
            "details": details or {},
            "level": level,
            "timestamp": datetime.utcnow()
        }
        
        # Update execution record with new step
        result = self.db[self.COLLECTION_NAME].update_one(
            {"execution_id": execution_id},
            {
                "$push": {"steps": step_record},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Also log to standard logger
        log_msg = f"[{execution_id}] {step}: {message}"
        if level == ExecutionLogLevel.ERROR:
            logger.error(log_msg)
        elif level == ExecutionLogLevel.WARNING:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        
        return step_record
    
    def complete_execution(
        self,
        execution_id: str,
        status: str = "completed",
        summary: Optional[Dict[str, Any]] = None
    ):
        """Mark an execution as completed"""
        self.db[self.COLLECTION_NAME].update_one(
            {"execution_id": execution_id},
            {
                "$set": {
                    "status": status,
                    "completed_at": datetime.utcnow(),
                    "summary": summary,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Execution {execution_id} completed with status: {status}")
    
    def fail_execution(
        self,
        execution_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """Mark an execution as failed"""
        # Log the error step
        self.log_step(
            execution_id,
            ExecutionStep.ERROR,
            error_message,
            error_details,
            ExecutionLogLevel.ERROR
        )
        
        # Update execution status
        self.db[self.COLLECTION_NAME].update_one(
            {"execution_id": execution_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.utcnow(),
                    "error": {
                        "message": error_message,
                        "details": error_details
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.error(f"Execution {execution_id} failed: {error_message}")
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution record by ID"""
        execution = self.db[self.COLLECTION_NAME].find_one(
            {"execution_id": execution_id}
        )
        if execution:
            execution["id"] = str(execution.pop("_id"))
        return execution
    
    def get_execution_by_order(self, order_id: str) -> List[Dict[str, Any]]:
        """Get all executions for an order"""
        executions = list(self.db[self.COLLECTION_NAME].find(
            {"order_id": order_id}
        ).sort("created_at", -1))
        
        for execution in executions:
            execution["id"] = str(execution.pop("_id"))
        
        return executions
    
    def get_recent_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent executions"""
        executions = list(self.db[self.COLLECTION_NAME].find().sort(
            "created_at", -1
        ).limit(limit))
        
        for execution in executions:
            execution["id"] = str(execution.pop("_id"))
        
        return executions
    
    def get_failed_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get failed executions"""
        executions = list(self.db[self.COLLECTION_NAME].find(
            {"status": "failed"}
        ).sort("created_at", -1).limit(limit))
        
        for execution in executions:
            execution["id"] = str(execution.pop("_id"))
        
        return executions
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        status_counts = list(self.db[self.COLLECTION_NAME].aggregate(pipeline))
        
        stats = {
            "total": 0,
            "by_status": {},
            "success_rate": 0.0
        }
        
        for item in status_counts:
            status = item["_id"]
            count = item["count"]
            stats["by_status"][status] = count
            stats["total"] += count
        
        if stats["total"] > 0:
            completed = stats["by_status"].get("completed", 0)
            stats["success_rate"] = round((completed / stats["total"]) * 100, 2)
        
        return stats


# Global logger instance
execution_logger = ExecutionLogger()
