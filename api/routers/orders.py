"""
Orders Router - Order API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from services.order_service import OrderService
from services.execution_logger import ExecutionLogger
from api.models.order import OrderResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])

order_service = OrderService()
execution_logger = ExecutionLogger()


# Request models for new simplified API
class CreateOrderRequest(BaseModel):
    """Request model for creating an order"""
    sku: str
    quantity: int
    store_id: str
    priority: Optional[str] = None  # high, normal, low


class CreateOrderLegacyRequest(BaseModel):
    """Legacy request model for backward compatibility"""
    store_id: str
    items: List[dict]
    shipping_address: Optional[dict] = None


@router.post("/create")
async def create_order_simple(request: CreateOrderRequest):
    """
    Create a new order (simplified API).
    
    Creates order with status 'pending'. 
    Use /orders/process/{order_id} to execute the order.
    """
    try:
        order = order_service.create_order(
            sku=request.sku,
            quantity=request.quantity,
            store_id=request.store_id,
            priority=request.priority
        )
        order["id"] = str(order["_id"])
        del order["_id"]
        return {
            "success": True,
            "message": f"Order created successfully. Use /orders/process/{order['order_id']} to process.",
            "order": order
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/process/{order_id}")
async def process_order(order_id: str):
    """
    Process an order through the execution pipeline.
    
    Pipeline:
    1. Validate order
    2. Select optimal warehouse
    3. Allocate inventory (reserve stock)
    4. Create delivery
    5. Update order status to 'allocated'
    
    Returns execution details including warehouse decision and delivery info.
    """
    try:
        result = order_service.process_order(order_id)
        
        # Clean up MongoDB ObjectIds for JSON response
        if result.get("order") and "_id" in result["order"]:
            result["order"]["id"] = str(result["order"]["_id"])
            del result["order"]["_id"]
        
        if result.get("delivery") and "_id" in result["delivery"]:
            result["delivery"]["id"] = str(result["delivery"]["_id"])
            del result["delivery"]["_id"]
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/ship")
async def ship_order(order_id: str):
    """
    Ship an order (transition from allocated to shipped).
    
    This confirms the inventory shipment and starts the delivery.
    """
    try:
        order = order_service.ship_order(order_id)
        order["id"] = str(order["_id"])
        del order["_id"]
        return {"success": True, "message": "Order shipped", "order": order}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error shipping order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/deliver")
async def deliver_order(order_id: str):
    """Mark order as delivered"""
    try:
        order = order_service.deliver_order(order_id)
        order["id"] = str(order["_id"])
        del order["_id"]
        return {"success": True, "message": "Order delivered", "order": order}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error delivering order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason")
):
    """Cancel an order"""
    try:
        order = order_service.cancel_order(order_id, reason)
        order["id"] = str(order["_id"])
        del order["_id"]
        return {"success": True, "message": "Order cancelled", "order": order}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("")
async def create_order_legacy(order_data: dict):
    """Create a new order (legacy API for backward compatibility)"""
    try:
        # For legacy API, use the old create method if items are provided
        if "items" in order_data:
            order = order_service.db.orders.find_one({"order_id": "test"})  # Check connection
            from services.order_service import OrderService as OS
            legacy_service = OS()
            # Fallback to direct insertion for legacy format
            import uuid
            from datetime import datetime
            
            order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            store = legacy_service.db.stores.find_one({"store_id": order_data["store_id"]})
            if not store:
                raise ValueError(f"Store {order_data['store_id']} not found")
            
            order = {
                "order_id": order_id,
                "store_id": order_data["store_id"],
                "items": order_data["items"],
                "total_amount": sum(item.get("total_price", 0) for item in order_data["items"]),
                "status": "pending",
                "priority": "normal",
                "order_date": datetime.utcnow(),
                "shipping_address": order_data.get("shipping_address", {
                    "city": store["location"]["city"],
                    "state": store["location"].get("state"),
                    "country": store["location"].get("country", "India")
                }),
                "assigned_warehouse": None,
                "delivery_id": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = legacy_service.db.orders.insert_one(order)
            order["_id"] = result.inserted_id
            order["id"] = str(order["_id"])
            del order["_id"]
            return order
        else:
            raise ValueError("Missing 'items' in request body")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats")
async def get_order_stats():
    """Get order statistics"""
    try:
        stats = order_service.get_order_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching order stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}")
async def get_order(order_id: str):
    """Get order by ID"""
    try:
        order = order_service.get_order(order_id)
        order["id"] = str(order["_id"])
        del order["_id"]
        return order
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
async def get_orders(
    store_id: Optional[str] = Query(None, description="Filter by store ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get orders with optional filters"""
    try:
        orders = order_service.get_orders(store_id, status, priority, limit)
        for order in orders:
            order["id"] = str(order["_id"])
            del order["_id"]
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    """Update order status"""
    try:
        order = order_service.update_order_status(order_id, status)
        order["id"] = str(order["_id"])
        del order["_id"]
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Execution logs endpoints
@router.get("/executions/recent")
async def get_recent_executions(limit: int = Query(50, ge=1, le=200)):
    """Get recent order executions"""
    try:
        executions = execution_logger.get_recent_executions(limit)
        return executions
    except Exception as e:
        logger.error(f"Error fetching executions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/executions/stats")
async def get_execution_stats():
    """Get execution statistics"""
    try:
        stats = execution_logger.get_execution_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching execution stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get execution details by ID"""
    try:
        execution = execution_logger.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
        return execution
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{order_id}/executions")
async def get_order_executions(order_id: str):
    """Get all executions for an order"""
    try:
        executions = execution_logger.get_execution_by_order(order_id)
        return executions
    except Exception as e:
        logger.error(f"Error fetching order executions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
