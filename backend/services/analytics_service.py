"""
Analytics Service - Advanced analytics and reporting
"""
from typing import Dict, Any, List
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced analytics and reporting"""
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def get_stock_velocity(self) -> Dict[str, float]:
        """Calculate stock velocity (units sold per day) - placeholder for future implementation"""
        # This would require historical sales data
        # For now, return a placeholder
        return {
            "average_velocity": 0.0,
            "high_velocity_products": 0,
            "low_velocity_products": 0
        }
    
    def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate system alerts based on current data"""
        alerts = []
        
        # Low stock alerts
        from api.config import settings
        low_stock_threshold = settings.low_stock_threshold
        critical_stock_threshold = settings.critical_stock_threshold
        
        low_stock_items = self.db.inventory.find(
            {"quantity": {"$lt": low_stock_threshold}}
        )
        
        for item in low_stock_items:
            alert_type = "critical" if item["quantity"] < critical_stock_threshold else "warning"
            alerts.append({
                "type": "low_stock",
                "severity": alert_type,
                "message": f"Low stock for SKU {item['sku']} at {item['location_id']}",
                "details": {
                    "sku": item["sku"],
                    "location_id": item["location_id"],
                    "current_quantity": item["quantity"],
                    "threshold": low_stock_threshold
                },
                "timestamp": item.get("last_stock_check", None)
            })
        
        # Warehouse utilization alerts
        warehouses = self.db.warehouses.find()
        for warehouse in warehouses:
            utilization = (warehouse["current_utilization"] / warehouse["capacity"] * 100) if warehouse["capacity"] > 0 else 0
            if utilization > 90:
                alerts.append({
                    "type": "warehouse_capacity",
                    "severity": "warning",
                    "message": f"Warehouse {warehouse['warehouse_id']} is at {utilization:.1f}% capacity",
                    "details": {
                        "warehouse_id": warehouse["warehouse_id"],
                        "current_utilization": warehouse["current_utilization"],
                        "capacity": warehouse["capacity"],
                        "utilization_rate": utilization
                    },
                    "timestamp": warehouse.get("updated_at", None)
                })
        
        logger.info(f"Generated {len(alerts)} alerts")
        return alerts
    
    def get_inventory_value(self) -> Dict[str, float]:
        """Calculate total inventory value"""
        pipeline = [
            {
                "$lookup": {
                    "from": "products",
                    "localField": "sku",
                    "foreignField": "sku",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": None,
                    "total_value": {
                        "$sum": {
                            "$multiply": ["$quantity", "$product.current_price"]
                        }
                    }
                }
            }
        ]
        
        result = list(self.db.inventory.aggregate(pipeline))
        if result:
            return {"total_inventory_value": round(result[0]["total_value"], 2)}
        return {"total_inventory_value": 0.0}
    
    def get_category_performance(self) -> List[Dict[str, Any]]:
        """Get performance metrics by product category"""
        pipeline = [
            {
                "$lookup": {
                    "from": "products",
                    "localField": "sku",
                    "foreignField": "sku",
                    "as": "product"
                }
            },
            {
                "$unwind": "$product"
            },
            {
                "$group": {
                    "_id": "$product.category",
                    "total_quantity": {"$sum": "$quantity"},
                    "total_revenue": {"$sum": "$product.total_revenue"},
                    "average_price": {"$avg": "$product.current_price"}
                }
            },
            {
                "$project": {
                    "category": "$_id",
                    "total_quantity": "$total_quantity",
                    "total_revenue": "$total_revenue",
                    "average_price": "$average_price"
                }
            }
        ]
        
        return list(self.db.inventory.aggregate(pipeline))
