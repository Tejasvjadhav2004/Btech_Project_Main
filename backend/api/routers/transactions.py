"""
Transactions API Router - Handle transaction-related endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from services.transaction_service import TransactionService, InsufficientStockError
from db.connection import mongodb

router = APIRouter()


# Pydantic models for request/response
class OrderItem(BaseModel):
    sku: str
    quantity: int
    location_id: Optional[str] = None


class Order(BaseModel):
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    items: List[OrderItem]


class RestockOrder(BaseModel):
    sku: str
    quantity: int
    location_id: str
    supplier_id: Optional[str] = None


class TransferOrder(BaseModel):
    sku: str
    quantity: int
    from_location: str
    to_location: str


# Dependency to get transaction service
def get_transaction_service():
    return TransactionService()


@router.post("/transactions/sale")
async def process_sale(order: Order, service: TransactionService = Depends(get_transaction_service)):
    """
    Process customer sale transaction
    
    Args:
        order: Order with items and customer info
    
    Returns:
        Transaction result
    """
    try:
        order_dict = order.dict()
        
        # Generate order_id if not provided
        if not order_dict.get('order_id'):
            import uuid
            order_dict['order_id'] = f"ORD{uuid.uuid4().hex[:8].upper()}"
        
        result = service.process_sale(order_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions/restock")
async def process_restock(restock: RestockOrder, service: TransactionService = Depends(get_transaction_service)):
    """
    Process inventory restock transaction
    
    Args:
        restock: Restock order details
    
    Returns:
        Transaction result
    """
    try:
        restock_dict = restock.dict()
        result = service.process_restock(restock_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transactions/transfer")
async def process_transfer(transfer: TransferOrder, service: TransactionService = Depends(get_transaction_service)):
    """
    Process inventory transfer between locations
    
    Args:
        transfer: Transfer order details
    
    Returns:
        Transaction result
    """
    try:
        transfer_dict = transfer.dict()
        result = service.process_transfer(transfer_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/{sku}/live")
async def get_live_inventory(sku: str, service: TransactionService = Depends(get_transaction_service)):
    """
    Get live inventory status for a product
    
    Args:
        sku: Product SKU
    
    Returns:
        Live inventory data
    """
    try:
        inventory = service.get_current_inventory(sku)
        
        if not inventory:
            raise HTTPException(status_code=404, detail=f"Inventory not found for SKU: {sku}")
        
        return inventory
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{sku}/history")
async def get_transaction_history(sku: str, limit: int = 100, service: TransactionService = Depends(get_transaction_service)):
    """
    Get transaction history for a product
    
    Args:
        sku: Product SKU
        limit: Maximum number of transactions to return
    
    Returns:
        List of transactions
    """
    try:
        transactions = service.get_transaction_history(sku, limit)
        return {"sku": sku, "transactions": transactions}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/low-stock")
async def get_low_stock_items(threshold: Optional[int] = None, service: TransactionService = Depends(get_transaction_service)):
    """
    Get items with low stock levels
    
    Args:
        threshold: Optional stock threshold
    
    Returns:
        List of low stock items
    """
    try:
        low_stock_items = service.get_low_stock_items(threshold)
        return {"low_stock_items": low_stock_items, "count": len(low_stock_items)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/status")
async def get_system_status(service: TransactionService = Depends(get_transaction_service)):
    """
    Get overall system status
    
    Returns:
        System status summary
    """
    try:
        status = service.get_system_status()
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/summary")
async def get_inventory_summary():
    """
    Get inventory summary statistics
    
    Returns:
        Inventory summary
    """
    try:
        db = mongodb.get_database()
        
        # Get inventory summary
        summary = list(db.inventory.aggregate([
            {
                '$group': {
                    '_id': '$location_type',
                    'total_items': {'$sum': '$current_stock'},
                    'total_products': {'$sum': 1},
                    'low_stock_count': {
                        '$sum': {
                            '$cond': [
                                {'$lt': ['$current_stock', '$reorder_threshold']},
                                1,
                                0
                            ]
                        }
                    },
                    'total_transactions': {'$sum': '$transactions_count'},
                    'total_sales': {'$sum': '$total_sales'}
                }
            }
        ]))
        
        result = {}
        for item in summary:
            location_type = item['_id']
            result[location_type] = {
                'total_items': item['total_items'],
                'total_products': item['total_products'],
                'low_stock_count': item['low_stock_count'],
                'total_transactions': item['total_transactions'],
                'total_sales': item['total_sales']
            }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/{sku}/locations")
async def get_inventory_locations(sku: str):
    """
    Get all locations where a product has inventory
    
    Args:
        sku: Product SKU
    
    Returns:
        List of inventory locations
    """
    try:
        db = mongodb.get_database()
        
        inventory_locations = list(db.inventory.find(
            {'sku': sku},
            {
                'location_id': 1,
                'location_type': 1,
                'current_stock': 1,
                'available_stock': 1,
                'reserved_stock': 1,
                '_id': 0
            }
        ))
        
        return {"sku": sku, "locations": inventory_locations}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/metrics")
async def get_dashboard_metrics():
    """
    Get comprehensive dashboard metrics
    
    Returns:
        Dashboard metrics
    """
    try:
        db = mongodb.get_database()
        
        # Get inventory metrics
        inventory_metrics = list(db.inventory.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_items': {'$sum': '$current_stock'},
                    'total_products': {'$sum': 1},
                    'low_stock_count': {
                        '$sum': {
                            '$cond': [
                                {'$lt': ['$current_stock', '$reorder_threshold']},
                                1,
                                0
                            ]
                        }
                    },
                    'total_transactions': {'$sum': '$transactions_count'},
                    'total_sales': {'$sum': '$total_sales'},
                    'total_restock': {'$sum': '$total_restock'}
                }
            }
        ]))
        
        # Get transaction metrics
        transaction_metrics = list(db.transactions.aggregate([
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1},
                    'total_quantity': {'$sum': '$quantity'}
                }
            }
        ]))
        
        result = {
            'inventory': inventory_metrics[0] if inventory_metrics else {},
            'transactions': {t['_id']: {'count': t['count'], 'total_quantity': t['total_quantity']} for t in transaction_metrics},
            'timestamp': datetime.utcnow()
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))