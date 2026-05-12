"""
Orchestration API Router

API endpoints for autonomous orchestration operations.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestration", tags=["Orchestration"])

# Import orchestrator
from orchestration.engine.orchestrator_service import orchestrator_service


# ============================================================
# REQUEST MODELS
# ============================================================

class ApprovalRequest(BaseModel):
    """Request model for approving workflow"""
    approved_by: str
    notes: Optional[str] = None


class RejectionRequest(BaseModel):
    """Request model for rejecting workflow"""
    rejected_by: str
    reason: str


class SignalTriggerRequest(BaseModel):
    """Request model for manually triggering orchestration"""
    signal_id: str
    signal_type: str
    severity: str = "medium"
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    product_id: Optional[str] = None
    details: Optional[dict] = None


# ============================================================
# WORKFLOW ENDPOINTS
# ============================================================

@router.get("/workflows")
async def get_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum results")
):
    """Get orchestration workflows"""
    try:
        workflows = await orchestrator_service.get_active_workflows(limit)

        if status:
            workflows = [w for w in workflows if w.get("status") == status]

        return {
            "workflows": workflows,
            "count": len(workflows)
        }
    except Exception as e:
        logger.error(f"Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_workflows():
    """Get all currently active workflows"""
    try:
        workflows = await orchestrator_service.get_active_workflows()

        return {
            "workflows": workflows,
            "count": len(workflows),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching active workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_workflow_history(
    hours: int = Query(24, description="Get workflows from last N hours"),
    limit: int = Query(100, description="Maximum results")
):
    """Get workflow history"""
    try:
        from orchestration.models.collections import get_workflows_collection

        collection = get_workflows_collection()
        since = datetime.utcnow() - timedelta(hours=hours)

        workflows = list(collection.find({
            "created_at": {"$gte": since}
        }).sort("created_at", -1).limit(limit))

        for w in workflows:
            w.pop("_id", None)

        return {
            "workflows": workflows,
            "count": len(workflows),
            "hours": hours
        }
    except Exception as e:
        logger.error(f"Error fetching workflow history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get specific workflow details"""
    workflow = await orchestrator_service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    # Get logs
    logs = await orchestrator_service.get_workflow_logs(workflow_id)

    return {
        "workflow": workflow,
        "logs": logs
    }


@router.get("/workflows/{workflow_id}/logs")
async def get_workflow_logs(workflow_id: str):
    """Get logs for a specific workflow"""
    logs = await orchestrator_service.get_workflow_logs(workflow_id)

    return {
        "workflow_id": workflow_id,
        "logs": logs,
        "count": len(logs)
    }


# ============================================================
# APPROVAL ENDPOINTS
# ============================================================

@router.get("/approvals")
async def get_pending_approvals(
    required_role: Optional[str] = Query(None, description="Filter by required role"),
    limit: int = Query(50, description="Maximum results")
):
    """Get pending approval requests"""
    from orchestration.approvals.approval_service import approval_service

    approvals = approval_service.get_pending_approvals(required_role, limit)

    return {
        "approvals": [a.dict() for a in approvals],
        "count": len(approvals)
    }


@router.post("/approve")
async def approve_workflow(
    workflow_id: str,
    request: ApprovalRequest,
    background_tasks: BackgroundTasks
):
    """
    Approve a workflow.

    This will initiate workflow execution.
    """
    try:
        result = await orchestrator_service.approve_workflow(
            workflow_id,
            request.approved_by,
            request.notes
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "approval": result.get("approval"),
            "execution": result.get("execution")
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject_workflow(
    workflow_id: str,
    request: RejectionRequest
):
    """Reject a workflow"""
    try:
        result = await orchestrator_service.reject_workflow(
            workflow_id,
            request.rejected_by,
            request.reason
        )

        return {
            "success": True,
            "workflow_id": workflow_id,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# EXECUTION ENDPOINTS
# ============================================================

@router.post("/execute")
async def trigger_orchestration(
    request: SignalTriggerRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger orchestration for a signal.

    This creates a new workflow and either executes it immediately
    or requests approval based on policies.
    """
    try:
        # Build signal document
        signal = {
            "signal_id": request.signal_id,
            "type": request.signal_type,
            "severity": request.severity,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "product_id": request.product_id,
            "details": request.details or {}
        }

        # Process signal
        result = await orchestrator_service.process_signal(signal)

        return {
            "success": result.get("success", False),
            "workflow_id": result.get("workflow_id"),
            "status": result.get("status"),
            "details": result
        }
    except Exception as e:
        logger.error(f"Error triggering orchestration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/retry")
async def retry_workflow(workflow_id: str):
    """Retry a failed workflow"""
    try:
        workflow = await orchestrator_service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        if workflow.get("status") not in ["failed", "rolled_back"]:
            raise HTTPException(status_code=400, detail="Can only retry failed workflows")

        # Execute workflow
        from orchestration.workflows.workflow_engine import workflow_engine
        from orchestration.models.schemas import Workflow

        workflow_obj = Workflow(**workflow)
        workflow_obj.status = "executing"

        result = await orchestrator_service._execute_workflow(workflow_obj)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error retrying workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# METRICS & MONITORING
# ============================================================

@router.get("/metrics")
async def get_orchestration_metrics():
    """Get orchestration performance metrics"""
    try:
        metrics = await orchestrator_service.get_orchestration_metrics()

        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def orchestration_health():
    """Get orchestrator health status"""
    try:
        from orchestration.models.schemas import OrchestrationHealth

        health = OrchestrationHealth(
            status="healthy" if orchestrator_service.is_active() else "inactive",
            orchestrator_active=orchestrator_service.is_active(),
            active_workflows=0,
            pending_approvals=0,
            issues=[]
        )

        # Get active workflows count
        try:
            workflows = await orchestrator_service.get_active_workflows()
            health.active_workflows = len([w for w in workflows if w.get("status") in ["executing", "monitoring"]])
        except Exception:
            health.issues.append("Could not fetch active workflows")

        # Get pending approvals
        try:
            from orchestration.approvals.approval_service import approval_service
            approvals = approval_service.get_pending_approvals(limit=1000)
            health.pending_approvals = len(approvals)
        except Exception:
            health.issues.append("Could not fetch pending approvals")

        return health.dict()
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies")
async def get_policies():
    """Get active orchestration policies"""
    from orchestration.policies.policy_engine import policy_engine

    policies = policy_engine.get_policy_summary()

    return {
        "policies": policies,
        "count": len(policies)
    }


@router.post("/start")
async def start_orchestrator():
    """Start the orchestrator service"""
    orchestrator_service.start()

    return {
        "success": True,
        "status": "started",
        "active": orchestrator_service.is_active()
    }


@router.post("/stop")
async def stop_orchestrator():
    """Stop the orchestrator service"""
    orchestrator_service.stop()

    return {
        "success": True,
        "status": "stopped",
        "active": orchestrator_service.is_active()
    }


# ============================================================
# INVENTORY REBALANCING
# ============================================================

@router.post("/rebalance")
async def trigger_inventory_rebalance(
    sku: Optional[str] = Query(None, description="Specific SKU to rebalance"),
    threshold: float = Query(0.3, description="Imbalance threshold (0.0-1.0)")
):
    """
    Trigger inventory rebalancing across warehouses.

    This analyzes stock levels and triggers transfers to balance inventory.
    """
    try:
        # Create rebalancing signal
        signal = {
            "signal_id": f"rebalance-{datetime.utcnow().timestamp()}",
            "type": "INVENTORY_REBALANCE",
            "severity": "medium",
            "entity_type": "system",
            "entity_id": "all",
            "details": {
                "sku": sku,
                "threshold": threshold,
                "triggered_by": "manual"
            }
        }

        result = await orchestrator_service.process_signal(signal)

        return {
            "success": True,
            "rebalance_triggered": True,
            "workflow_id": result.get("workflow_id"),
            "details": result
        }
    except Exception as e:
        logger.error(f"Error triggering rebalance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_orchestration_suggestions():
    """
    Get AI-generated orchestration suggestions.

    This uses contextual analysis to suggest actions.
    """
    try:
        from orchestration.context.context_service import context_service

        # Get system-wide context
        context = context_service.get_system_wide_context()

        # Generate suggestions (simplified - in production would use LLM)
        suggestions = []

        if context.get("inventory", {}).get("low_stock_count", 0) > 5:
            suggestions.append({
                "type": "replenishment",
                "priority": "high",
                "description": f"Multiple items ({context['inventory']['low_stock_count']}) below reorder threshold",
                "recommended_action": "Review and approve pending replenishment orders"
            })

        if context.get("signals", {}).get("critical", 0) > 0:
            suggestions.append({
                "type": "immediate_action",
                "priority": "critical",
                "description": f"{context['signals']['critical']} critical signals require attention",
                "recommended_action": "Review and mitigate critical signals immediately"
            })

        if context.get("warehouses", {}).get("avg_utilization_percent", 0) > 85:
            suggestions.append({
                "type": "capacity_planning",
                "priority": "medium",
                "description": f"Average warehouse utilization at {context['warehouses']['avg_utilization_percent']:.1f}%",
                "recommended_action": "Consider warehouse expansion or load balancing"
            })

        return {
            "suggestions": suggestions,
            "context": context,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from datetime import timedelta


# ============================================================
# AUTO PROCESSOR ENDPOINTS
# ============================================================

@router.get("/auto-processor/status")
async def get_auto_processor_status():
    """
    Get auto processor status.

    Shows whether signals are being automatically processed through orchestration.
    """
    from orchestration.auto_processor import auto_processor

    return auto_processor.get_status()


@router.post("/auto-processor/trigger")
async def trigger_auto_processing():
    """
    Manually trigger signal processing.

    This immediately processes all active critical/high severity signals.
    """
    from orchestration.auto_processor import auto_processor

    if not auto_processor.is_active():
        raise HTTPException(
            status_code=400,
            detail="Auto processor is not active"
        )

    # Trigger immediate processing
    await auto_processor._process_signals()

    return {
        "success": True,
        "message": "Signal processing triggered",
        "status": auto_processor.get_status()
    }
