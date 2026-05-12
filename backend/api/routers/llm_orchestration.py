"""
LLM Orchestration API Router

API endpoints for LLM-powered autonomous orchestration.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm-orchestration", tags=["LLM Orchestration"])

# Import services
from services.llm_orchestrator_service import llm_orchestrator_service
from services.validation_service import validation_service
from services.context_service import context_service


# ============================================================
# REQUEST MODELS
# ============================================================

class GeneratePlanRequest(BaseModel):
    """Request to generate orchestration plan"""
    signal_id: Optional[str] = None
    signal_type: Optional[str] = None
    entity_id: Optional[str] = None
    dry_run: bool = True


class ExecutePlanRequest(BaseModel):
    """Request to execute a plan"""
    plan_id: str
    actions: List[dict]


# ============================================================
# ORCHESTRATION ENDPOINTS
# ============================================================

@router.get("/context")
async def get_operational_context():
    """
    Get aggregated operational context.

    Returns summarized context from all system components.
    """
    try:
        context = context_service.aggregate_context()
        return {
            "success": True,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan")
async def generate_orchestration_plan(
    request: GeneratePlanRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate an orchestration plan using LLM reasoning.

    This is the main endpoint for AI-driven decision making.

    The plan includes:
    - Situation analysis
    - Recommended actions
    - Reasoning chain
    - Risk assessment
    - Confidence score
    """
    try:
        # Build signal if provided
        signal = None
        if request.signal_id:
            signal = {
                "signal_id": request.signal_id,
                "type": request.signal_type or "unknown",
                "entity_id": request.entity_id
            }

        # Generate plan
        result = llm_orchestrator_service.generate_plan(
            signal=signal,
            dry_run=request.dry_run
        )

        return result

    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_orchestration_plan(request: ExecutePlanRequest):
    """
    Validate and execute an orchestration plan.

    All actions are validated before execution.
    Invalid actions are rejected with specific errors.
    """
    try:
        # Validate all actions
        validation_results = validation_service.validate_plan(request.actions)

        # Check if all actions are valid
        errors = [r for r in validation_results if not r.valid]
        if errors:
            return {
                "success": False,
                "plan_id": request.plan_id,
                "error": "Validation failed",
                "validation_errors": [
                    {
                        "action_id": e.action_id,
                        "errors": e.errors
                    }
                    for e in errors
                ]
            }

        # Execute actions
        from orchestration.agents import execution_agent

        execution_results = []
        for action in request.actions:
            result = execution_agent.execute_action(action, dry_run=False)
            execution_results.append(result)

        return {
            "success": True,
            "plan_id": request.plan_id,
            "execution_results": execution_results,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_orchestration_history(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get orchestration decision history.

    Returns recent decisions with context and actions.
    """
    try:
        history = llm_orchestrator_service.get_history(limit)
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }

    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decision/{decision_id}")
async def get_decision(decision_id: str):
    """
    Get a specific orchestration decision.
    """
    decision = llm_orchestrator_service.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

    return {
        "success": True,
        "decision": decision
    }


@router.get("/explanation/{decision_id}")
async def explain_decision(decision_id: str):
    """
    Get detailed explanation for an orchestration decision.

    Includes:
    - Full reasoning chain
    - Context at decision time
    - Risk assessment
    - Expected outcomes
    - Agent insights
    """
    explanation = llm_orchestrator_service.explain_decision(decision_id)

    if "error" in explanation:
        raise HTTPException(status_code=404, detail=explanation["error"])

    return {
        "success": True,
        "explanation": explanation
    }


@router.get("/metrics")
async def get_orchestration_metrics():
    """
    Get orchestration performance metrics.
    """
    try:
        metrics = llm_orchestrator_service.get_metrics()
        return {
            "success": True,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AGENT ENDPOINTS
# ============================================================

@router.post("/agents/sensing/run")
async def run_sensing_agent():
    """Run sensing agent analysis"""
    try:
        context = context_service.aggregate_context()
        result = llm_orchestrator_service._run_agents(context)["sensing"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/forecasting/run")
async def run_forecasting_agent():
    """Run forecasting agent analysis"""
    try:
        context = context_service.aggregate_context()
        result = llm_orchestrator_service._run_agents(context)["forecasting"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/optimization/run")
async def run_optimization_agent():
    """Run optimization agent analysis"""
    try:
        context = context_service.aggregate_context()
        result = llm_orchestrator_service._run_agents(context)["optimization"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# VALIDATION ENDPOINTS
# ============================================================

@router.post("/validate")
async def validate_actions(actions: List[dict]):
    """
    Validate a list of actions without executing.

    Returns validation results for each action.
    """
    try:
        results = validation_service.validate_plan(actions)
        return {
            "success": True,
            "all_valid": all(r.valid for r in results),
            "results": [r.dict() for r in results]
        }

    except Exception as e:
        logger.error(f"Error validating actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AUTONOMOUS PIPELINE
# ============================================================

@router.post("/pipeline/run")
async def run_autonomous_pipeline(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(True, description="If true, plan without executing")
):
    """
    Run the complete autonomous orchestration pipeline.

    Pipeline:
    1. Aggregate context
    2. Run agents
    3. Generate LLM decision
    4. Validate actions
    5. Execute (if not dry_run)

    This is the main autonomous operation endpoint.
    """
    try:
        result = llm_orchestrator_service.generate_plan(dry_run=dry_run)
        return result

    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/signal/{signal_id}")
async def process_signal_pipeline(
    signal_id: str,
    background_tasks: BackgroundTasks
):
    """
    Process a specific signal through the orchestration pipeline.

    Generates a targeted plan for the signal.
    """
    try:
        # Get signal from database
        from db.connection import mongodb
        signal = mongodb.get_database().signals.find_one({"signal_id": signal_id})

        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

        # Process through pipeline
        result = llm_orchestrator_service.generate_plan(signal=signal, dry_run=False)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing signal pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# HEALTH & STATUS
# ============================================================

@router.get("/health")
async def orchestration_health():
    """
    Get LLM orchestration health status.
    """
    try:
        # Check database connection
        from db.connection import mongodb
        db_connected = mongodb.get_database() is not None

        # Check if collections exist
        collections = mongodb.get_database().list_collection_names()
        history_exists = "orchestration_history" in collections

        # Get context
        context = context_service.aggregate_context()

        return {
            "status": "healthy" if db_connected else "unhealthy",
            "database_connected": db_connected,
            "history_collection_ready": history_exists,
            "context_available": len(context) > 0,
            "active_signals": context.get("signals", {}).get("total_active", 0),
            "critical_issues": len(context.get("critical_issues", [])),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/setup")
async def setup_orchestration():
    """
    Initialize orchestration collections and indexes.
    """
    try:
        llm_orchestrator_service.setup_collections()
        return {
            "success": True,
            "message": "Orchestration layer initialized"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
