"""
Signals Router - API endpoints for Sensing & Intelligence Layer
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from services.signal_service import SignalService, SignalType, SignalStatus
from services.sensing_service import SensingService
from services.decision_service import DecisionService
from services.scheduler_service import scheduler_service
from db.collections import setup_intelligence_collections, verify_collections
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["Signals & Intelligence"])

# Service instances
signal_service = SignalService()
sensing_service = SensingService()
decision_service = DecisionService()


# ========================================
# SIGNAL ENDPOINTS
# ========================================

@router.get("")
async def get_signals(
    status: Optional[str] = Query(None, description="Filter by status (active, acknowledged, resolved, expired)"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hours: Optional[int] = Query(None, description="Get signals from last N hours"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get signals with optional filters"""
    since = None
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
    
    signals = signal_service.get_signals(
        status=status,
        signal_type=signal_type,
        entity_type=entity_type,
        severity=severity,
        since=since,
        limit=limit
    )
    
    return {
        "signals": signals,
        "count": len(signals),
        "filters": {
            "status": status,
            "signal_type": signal_type,
            "entity_type": entity_type,
            "severity": severity,
            "hours": hours
        }
    }


@router.get("/active")
async def get_active_signals(
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get all active signals"""
    signals = signal_service.get_active_signals(
        signal_type=signal_type,
        severity=severity,
        limit=limit
    )
    
    return {
        "signals": signals,
        "count": len(signals),
        "status": "active"
    }


@router.get("/stats")
async def get_signal_stats():
    """Get signal statistics"""
    return signal_service.get_signal_stats()


# ========================================
# REPLENISHMENT ORDERS (Must be before /{signal_id} to avoid routing conflicts)
# ========================================

@router.get("/replenishment-orders")
async def get_replenishment_orders():
    """Get pending replenishment orders"""
    orders = decision_service.get_pending_replenishment_orders()
    return {"orders": orders, "count": len(orders)}


@router.post("/replenishment-orders/{order_id}/approve")
async def approve_replenishment_order(order_id: str):
    """Approve a replenishment order"""
    result = decision_service.approve_replenishment_order(order_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Order not found"))
    return result


# ========================================
# SCHEDULER ENDPOINTS (Must be before /{signal_id} to avoid routing conflicts)
# ========================================

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and job information"""
    return scheduler_service.get_status()


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the background scheduler"""
    scheduler_service.start()
    return {"message": "Scheduler started", "status": scheduler_service.get_status()}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the background scheduler"""
    scheduler_service.stop()
    return {"message": "Scheduler stopped", "status": scheduler_service.get_status()}


@router.post("/scheduler/pause")
async def pause_scheduler():
    """Pause all scheduled jobs"""
    scheduler_service.pause()
    return {"message": "Scheduler paused"}


@router.post("/scheduler/resume")
async def resume_scheduler():
    """Resume all scheduled jobs"""
    scheduler_service.resume()
    return {"message": "Scheduler resumed"}


@router.get("/scheduler/jobs")
async def get_scheduler_jobs():
    """Get all scheduled jobs"""
    return {"jobs": scheduler_service.get_all_jobs()}


@router.get("/scheduler/jobs/{job_id}")
async def get_job_info(job_id: str):
    """Get information about a specific job"""
    job = scheduler_service.get_job_info(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.post("/scheduler/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """Run a specific job immediately"""
    result = scheduler_service.run_job_now(job_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Job execution failed"))
    return result


@router.post("/scheduler/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a specific job"""
    scheduler_service.pause_job(job_id)
    return {"message": f"Job {job_id} paused"}


@router.post("/scheduler/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a specific job"""
    scheduler_service.resume_job(job_id)
    return {"message": f"Job {job_id} resumed"}


@router.get("/health")
async def intelligence_health():
    """Health check for intelligence layer"""
    collections_status = verify_collections()
    scheduler_status = scheduler_service.get_status()
    signal_stats = signal_service.get_signal_stats()
    
    return {
        "status": "healthy",
        "collections": collections_status,
        "scheduler": {
            "is_running": scheduler_status["is_running"],
            "job_count": scheduler_status["job_count"]
        },
        "signals": {
            "active": signal_stats.get("active_signals", 0),
            "total": signal_stats.get("total_signals", 0)
        }
    }


@router.get("/{signal_id}")
async def get_signal(signal_id: str):
    """Get a specific signal by ID"""
    signal = signal_service.get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    return signal


@router.post("/{signal_id}/acknowledge")
async def acknowledge_signal(signal_id: str):
    """Acknowledge a signal"""
    result = signal_service.acknowledge_signal(signal_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found or not active")
    return {"message": "Signal acknowledged", "signal": result}


@router.post("/{signal_id}/resolve")
async def resolve_signal(
    signal_id: str,
    note: Optional[str] = Query(None, description="Resolution note")
):
    """Resolve a signal"""
    result = signal_service.resolve_signal(
        signal_id,
        auto_resolved=False,
        resolution_note=note
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found or already resolved")
    return {"message": "Signal resolved", "signal": result}


# ========================================
# DETECTION ENDPOINTS
# ========================================

@router.post("/detect/low-stock")
async def run_low_stock_detection(
    threshold: Optional[int] = Query(None, description="Custom threshold"),
    location_type: Optional[str] = Query(None, description="Filter by location type")
):
    """Run low stock detection manually"""
    result = sensing_service.detect_low_stock(
        threshold=threshold,
        location_type=location_type,
        source="manual"
    )
    return result


@router.post("/detect/stockout")
async def run_stockout_detection(
    location_type: Optional[str] = Query(None, description="Filter by location type")
):
    """Run stockout detection manually"""
    result = sensing_service.detect_stockout(
        location_type=location_type,
        source="manual"
    )
    return result


@router.post("/detect/delivery-delay")
async def run_delivery_delay_detection(
    delay_hours: Optional[int] = Query(None, description="Minimum delay hours")
):
    """Run delivery delay detection manually"""
    result = sensing_service.detect_delivery_delay(
        delay_hours=delay_hours,
        source="manual"
    )
    return result


@router.post("/detect/demand-spike")
async def run_demand_spike_detection(
    threshold: Optional[float] = Query(None, description="Spike threshold multiplier"),
    hours: int = Query(24, description="Time window in hours")
):
    """Run demand spike detection manually"""
    result = sensing_service.detect_demand_spike(
        threshold=threshold,
        hours=hours,
        source="manual"
    )
    return result


@router.post("/detect/utilization")
async def run_utilization_detection():
    """Run warehouse utilization detection manually"""
    over = sensing_service.detect_over_utilization(source="manual")
    under = sensing_service.detect_under_utilization(source="manual")
    return {
        "over_utilization": over,
        "under_utilization": under
    }


@router.post("/detect/all")
async def run_all_detections():
    """Run all detection functions manually"""
    result = sensing_service.run_all_detections(source="manual")
    return result


# ========================================
# DECISION ENGINE ENDPOINTS
# ========================================

@router.post("/process/{signal_id}")
async def process_signal(signal_id: str):
    """Process a specific signal through the decision engine"""
    result = decision_service.process_signal(signal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))
    return result


@router.post("/process-all")
async def process_all_active_signals(
    auto_only: bool = Query(True, description="Only process auto-processable signals")
):
    """Process all active signals through the decision engine"""
    result = decision_service.process_active_signals(auto_only=auto_only)
    return result


@router.get("/decision-stats")
async def get_decision_stats():
    """Get decision engine statistics"""
    return decision_service.get_decision_stats()


# ========================================
# ALERTS & ESCALATIONS
# ========================================

@router.get("/alerts")
async def get_alerts(
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get alerts"""
    alerts = decision_service.get_alerts(
        acknowledged=acknowledged,
        severity=severity,
        limit=limit
    )
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    result = decision_service.acknowledge_alert(alert_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


# ========================================
# EVENT LOGS
# ========================================

@router.get("/event-logs")
async def get_event_logs(
    signal_id: Optional[str] = Query(None, description="Filter by signal ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    hours: Optional[int] = Query(None, description="Get logs from last N hours"),
    limit: int = Query(100, description="Maximum number of results")
):
    """Get event logs"""
    since = None
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
    
    events = signal_service.get_event_logs(
        signal_id=signal_id,
        event_type=event_type,
        source=source,
        since=since,
        limit=limit
    )
    
    return {"events": events, "count": len(events)}


# ========================================
# SETUP & HEALTH
# ========================================

@router.post("/setup")
async def setup_collections():
    """Set up intelligence layer collections and indexes"""
    success = setup_intelligence_collections()
    if success:
        return {"message": "Intelligence collections setup complete"}
    raise HTTPException(status_code=500, detail="Failed to setup collections")



