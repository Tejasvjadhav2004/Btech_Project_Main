"""
Dashboard Router - Dashboard API endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional
from services.monitoring_service import MonitoringService
from services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

monitoring_service = MonitoringService()
analytics_service = AnalyticsService()


@router.get("/overview")
async def get_dashboard_overview():
    """Get system overview KPIs"""
    kpis = monitoring_service.get_kpis()
    return kpis


@router.get("/product-stock")
async def get_product_stock(sku: Optional[str] = Query(None, description="Filter by SKU")):
    """Get stock distribution by product"""
    distribution = monitoring_service.get_product_distribution(sku)
    return {"distribution": distribution}


@router.get("/warehouse-stock")
async def get_warehouse_stock():
    """Get stock by warehouse"""
    utilization = monitoring_service.warehouse_utilization()
    return {"warehouses": utilization}


@router.get("/store-stock")
async def get_store_stock():
    """Get stock by store"""
    from db.connection import get_db
    db = get_db()
    
    stores = list(db.stores.find({}, {"_id": 0, "store_id": 1, "name": 1, "current_utilization": 1}))
    return {"stores": stores}


@router.get("/low-stock")
async def get_low_stock(threshold: int = Query(20, ge=0, description="Low stock threshold")):
    """Get low stock alerts"""
    low_stock = monitoring_service.detect_low_stock(threshold)
    return {
        "count": len(low_stock),
        "items": low_stock
    }


@router.get("/metrics")
async def get_metrics():
    """Get detailed metrics"""
    kpis = monitoring_service.get_kpis()
    stock_by_category = monitoring_service.get_stock_by_category()
    top_products = monitoring_service.get_top_products_by_revenue(10)
    alerts = analytics_service.generate_alerts()
    inventory_value = analytics_service.get_inventory_value()
    
    return {
        "kpis": kpis,
        "stock_by_category": stock_by_category,
        "top_products": top_products,
        "alerts": alerts,
        "inventory_value": inventory_value
    }
