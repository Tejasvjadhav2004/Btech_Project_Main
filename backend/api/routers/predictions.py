"""
Predictions Router - API endpoints for predictive intelligence

Provides endpoints for:
- Demand predictions
- Stockout risk predictions
- Delay risk predictions
- Predictive signals
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])


@router.get("/demand")
async def get_demand_predictions(
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    limit: int = Query(100, ge=1, le=500)
) -> List[Dict[str, Any]]:
    """
    Get demand predictions for products.

    Returns predicted demand for the next 7 days per SKU-Store combination.

    Args:
        sku: Optional SKU filter
        store_id: Optional store ID filter
        limit: Maximum number of results

    Returns:
        List of demand predictions
    """
    try:
        from ml.inference.predict_demand_service import demand_prediction_service

        predictions = demand_prediction_service.get_predictions(
            sku=sku, store_id=store_id, limit=limit
        )

        return predictions

    except Exception as e:
        logger.error(f"Error fetching demand predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand/{sku}/{store_id}")
async def get_demand_prediction_for_sku_store(
    sku: str,
    store_id: str,
    days_ahead: int = Query(7, ge=1, le=30, description="Days to predict ahead")
) -> Dict[str, Any]:
    """
    Get demand prediction for a specific SKU at a store.

    Args:
        sku: Product SKU
        store_id: Store ID
        days_ahead: Number of days to predict

    Returns:
        Detailed demand prediction
    """
    try:
        from ml.inference.predict_demand_service import demand_prediction_service

        prediction = demand_prediction_service.predict_demand(
            sku=sku, store_id=store_id, days_ahead=days_ahead
        )

        return prediction

    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demand/generate")
async def generate_all_demand_predictions() -> Dict[str, Any]:
    """
    Generate demand predictions for all active inventory items.

    This triggers the ML model to generate predictions for all products.
    Usually called by the scheduler, but can be triggered manually.

    Returns:
        Generation summary
    """
    try:
        from ml.inference.predict_demand_service import demand_prediction_service

        result = demand_prediction_service.generate_all_predictions(days_ahead=7)

        return result

    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stockout-risk")
async def get_stockout_risks(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200)
) -> List[Dict[str, Any]]:
    """
    Get predicted stockout risks.

    Returns a list of products predicted to stock out based on
    current inventory and demand forecasts.

    Args:
        severity: Optional severity filter (low, medium, high, critical)
        limit: Maximum number of results

    Returns:
        List of stockout risk predictions
    """
    try:
        from services.predictive_sensing_service import predictive_sensing_service

        risks = predictive_sensing_service.get_predictive_risks(
            risk_type="PREDICTED_STOCKOUT",
            severity=severity,
            limit=limit
        )

        return risks

    except Exception as e:
        logger.error(f"Error fetching stockout risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/delay-risk")
async def get_delay_risks(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200)
) -> List[Dict[str, Any]]:
    """
    Get predicted delivery delay risks.

    Returns a list of deliveries predicted to be delayed.

    Args:
        severity: Optional severity filter
        limit: Maximum number of results

    Returns:
        List of delay risk predictions
    """
    try:
        from services.predictive_sensing_service import predictive_sensing_service

        risks = predictive_sensing_service.get_predictive_risks(
            risk_type="PREDICTED_DELAY",
            severity=severity,
            limit=limit
        )

        return risks

    except Exception as e:
        logger.error(f"Error fetching delay risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-risks")
async def get_all_predictive_risks(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=500)
) -> List[Dict[str, Any]]:
    """
    Get all predictive risks.

    Returns all active predictive risk signals.

    Args:
        severity: Optional severity filter
        limit: Maximum number of results

    Returns:
        List of all predictive risks
    """
    try:
        from services.predictive_sensing_service import predictive_sensing_service

        risks = predictive_sensing_service.get_predictive_risks(
            severity=severity,
            limit=limit
        )

        return risks

    except Exception as e:
        logger.error(f"Error fetching predictive risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-predictive-sensing")
async def run_predictive_sensing() -> Dict[str, Any]:
    """
    Manually trigger predictive sensing detection.

    Runs all predictive detection functions to identify future risks.

    Returns:
        Detection results
    """
    try:
        from services.predictive_sensing_service import predictive_sensing_service

        result = predictive_sensing_service.run_all_predictive_detections(
            source="manual_trigger"
        )

        return result

    except Exception as e:
        logger.error(f"Error running predictive sensing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-demand")
async def get_high_demand_items(
    threshold: int = Query(50, ge=1, description="Minimum predicted demand")
) -> List[Dict[str, Any]]:
    """
    Get items with high predicted demand.

    Args:
        threshold: Minimum predicted demand threshold

    Returns:
        List of high-demand items
    """
    try:
        from ml.inference.predict_demand_service import demand_prediction_service

        items = demand_prediction_service.get_high_demand_items(threshold=threshold)

        return items

    except Exception as e:
        logger.error(f"Error fetching high demand items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-status")
async def get_model_status() -> Dict[str, Any]:
    """
    Get the status of the ML models.

    Returns information about loaded models and their performance.
    """
    try:
        from ml.utils.artifact_manager import artifact_manager

        models = artifact_manager.list_models()

        demand_model_metadata = artifact_manager.load_metadata("demand_forecast_model")

        return {
            "models_available": len(models),
            "demand_forecast_model": {
                "exists": artifact_manager.model_exists("demand_forecast_model"),
                "metadata": demand_model_metadata
            },
            "all_models": models,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-model")
async def train_demand_model() -> Dict[str, Any]:
    """
    Train the demand forecasting model.

    This endpoint triggers the model training pipeline.
    Uses Random Forest as the underlying model.

    Returns:
        Training results
    """
    try:
        from ml.training.train_demand_forecast import DemandForecastTrainer

        trainer = DemandForecastTrainer(model_type="random_forest")
        result = trainer.train()

        return result

    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
