"""
Deliveries Router - Delivery API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.delivery_service import DeliveryService
from api.models.delivery import DeliveryResponse, DeliveryCreate, DeliveryUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])

delivery_service = DeliveryService()


@router.get("", response_model=List[dict])
async def get_deliveries(
    status: Optional[str] = Query(None, description="Filter by status"),
    warehouse_id: Optional[str] = Query(None, description="Filter by source warehouse"),
    store_id: Optional[str] = Query(None, description="Filter by destination store"),
    limit: int = Query(100, ge=1, le=1000, description="Max results")
):
    """Get deliveries with optional filters"""
    try:
        deliveries = delivery_service.get_deliveries(
            status=status,
            warehouse_id=warehouse_id,
            store_id=store_id,
            limit=limit
        )
        return deliveries
    except Exception as e:
        logger.error(f"Error fetching deliveries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_delivery_stats():
    """Get delivery statistics"""
    try:
        stats = delivery_service.get_delivery_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching delivery stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{delivery_id}")
async def get_delivery(delivery_id: str):
    """Get delivery by ID"""
    try:
        delivery = delivery_service.get_delivery(delivery_id)
        if not delivery:
            raise HTTPException(status_code=404, detail=f"Delivery {delivery_id} not found")
        return delivery
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching delivery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/order/{order_id}")
async def get_delivery_by_order(order_id: str):
    """Get delivery for an order"""
    try:
        delivery = delivery_service.get_delivery_by_order(order_id)
        if not delivery:
            raise HTTPException(status_code=404, detail=f"No delivery found for order {order_id}")
        return delivery
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching delivery for order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{delivery_id}/status")
async def update_delivery_status(
    delivery_id: str,
    status: str = Query(..., description="New status: pending, in_transit, delivered, failed, cancelled")
):
    """Update delivery status"""
    try:
        delivery = delivery_service.update_delivery_status(delivery_id, status)
        return delivery
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating delivery status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{delivery_id}/start")
async def start_delivery(delivery_id: str):
    """Start a delivery (mark as in_transit)"""
    try:
        delivery = delivery_service.start_delivery(delivery_id)
        return delivery
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting delivery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{delivery_id}/complete")
async def complete_delivery(delivery_id: str):
    """Complete a delivery (mark as delivered)"""
    try:
        delivery = delivery_service.complete_delivery(delivery_id)
        return delivery
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing delivery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{delivery_id}/cancel")
async def cancel_delivery(
    delivery_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason")
):
    """Cancel a delivery"""
    try:
        delivery = delivery_service.cancel_delivery(delivery_id, reason)
        return delivery
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling delivery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
