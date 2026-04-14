"""
Forecast Router - Demand Forecast API endpoints
"""
from fastapi import APIRouter
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/forecast", tags=["Forecast"])


@router.get("")
async def get_forecast() -> List[Dict[str, Any]]:
    """
    Get demand forecast data with predicted vs actual demand
    Returns mock data for demonstration purposes
    """
    # Mock forecast data - in production this would come from ML models
    forecast_data = [
        {
            "id": 1,
            "month": "Jan",
            "predicted": 1500,
            "actual": 1450
        },
        {
            "id": 2,
            "month": "Feb",
            "predicted": 1600,
            "actual": 1620
        },
        {
            "id": 3,
            "month": "Mar",
            "predicted": 1400,
            "actual": 1380
        },
        {
            "id": 4,
            "month": "Apr",
            "predicted": 1550,
            "actual": 1580
        },
        {
            "id": 5,
            "month": "May",
            "predicted": 1700,
            "actual": 1680
        },
        {
            "id": 6,
            "month": "Jun",
            "predicted": 1850,
            "actual": 1900
        },
        {
            "id": 7,
            "month": "Jul",
            "predicted": 1950,
            "actual": 1920
        },
        {
            "id": 8,
            "month": "Aug",
            "predicted": 1800,
            "actual": 1780
        },
        {
            "id": 9,
            "month": "Sep",
            "predicted": 1650,
            "actual": 1700
        },
        {
            "id": 10,
            "month": "Oct",
            "predicted": 1750,
            "actual": 1720
        },
        {
            "id": 11,
            "month": "Nov",
            "predicted": 1900,
            "actual": 1950
        },
        {
            "id": 12,
            "month": "Dec",
            "predicted": 2100,
            "actual": 2050
        }
    ]
    
    logger.info(f"Returning forecast data with {len(forecast_data)} months")
    return forecast_data


@router.get("/by-product/{sku}")
async def get_forecast_by_product(sku: str) -> Dict[str, Any]:
    """
    Get demand forecast for a specific product
    """
    # Mock product-specific forecast
    return {
        "sku": sku,
        "forecast": [
            {
                "id": 1,
                "month": "Jan",
                "predicted": 120,
                "actual": 115
            },
            {
                "id": 2,
                "month": "Feb",
                "predicted": 130,
                "actual": 135
            },
            {
                "id": 3,
                "month": "Mar",
                "predicted": 110,
                "actual": 108
            }
        ],
        "accuracy": 95.2,
        "trend": "increasing"
    }


@router.get("/summary")
async def get_forecast_summary() -> Dict[str, Any]:
    """
    Get forecast summary statistics
    """
    return {
        "total_months": 12,
        "average_accuracy": 94.8,
        "total_predicted": 20750,
        "total_actual": 20810,
        "variance": -60,
        "trend": "increasing",
        "seasonality": "moderate"
    }
