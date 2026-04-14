"""
Monitoring Service - Stock monitoring and analytics
"""
from typing import Dict, Any, List
from db.connection import mongodb
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    """Monitoring service for stock and operations"""
    
    def __init__(self):
        self.db = mongodb.get_database()
    
    def get_total_stock(self) -> Dict[str, Any]:
        """Calculate total stock across all locations"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_quantity": {"$sum": "$quantity"}
                }
            }
        ]
        result = list(self.db.inventory.aggregate(pipeline))
        
        if result:
            return {
                "total_stock": result[0]["total_quantity"],
                "total_products": self.db.products.count_documents({}),
                "total_locations": self.db.warehouses.count_documents({}) + self.db.stores.count_documents({})
            }
        return {"total_stock": 0, "total_products": 0, "total_locations": 0}
    
    def get_product_distribution(self, sku: str = None) -> List[Dict[str, Any]]:
        """Get stock distribution for a product across locations"""
        query = {"sku": sku} if sku else {}
        
        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {"location_id": "$location_id", "location_type": "$location_type"},
                    "quantity": {"$sum": "$quantity"}
                }
            },
            {
                "$project": {
                    "location_id": "$_id.location_id",
                    "location_type": "$_id.location_type",
                    "quantity": "$quantity"
                }
            }
        ]
        
        return list(self.db.inventory.aggregate(pipeline))
    
    def detect_low_stock(self, threshold: int = None) -> List[Dict[str, Any]]:
        """Identify products with stock below threshold"""
        if threshold is None:
            threshold = settings.low_stock_threshold
        
        low_stock = self.db.inventory.find(
            {"quantity": {"$lt": threshold}},
            {"_id": 0, "sku": 1, "location_id": 1, "location_type": 1, "quantity": 1}
        )
        
        return list(low_stock)
    
    def warehouse_utilization(self) -> List[Dict[str, Any]]:
        """Calculate warehouse capacity utilization"""
        warehouses = self.db.warehouses.find({}, {"_id": 0})
        
        utilization_data = []
        for warehouse in warehouses:
            capacity = warehouse.get("capacity", 1)
            current = warehouse.get("current_utilization", 0)
            utilization_rate = (current / capacity * 100) if capacity > 0 else 0
            
            utilization_data.append({
                "warehouse_id": warehouse["warehouse_id"],
                "name": warehouse["name"],
                "capacity": capacity,
                "current_utilization": current,
                "utilization_rate": round(utilization_rate, 2)
            })
        
        return utilization_data
    
    def get_kpis(self) -> Dict[str, Any]:
        """Get key performance indicators"""
        total_stock = self.get_total_stock()
        low_stock_alerts = len(self.detect_low_stock())
        warehouse_util = self.warehouse_utilization()
        
        # Calculate average warehouse utilization
        avg_util = sum(w["utilization_rate"] for w in warehouse_util) / len(warehouse_util) if warehouse_util else 0
        
        # Get total revenue
        revenue_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$total_revenue"}
                }
            }
        ]
        revenue_result = list(self.db.products.aggregate(revenue_pipeline))
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
        
        return {
            "total_products": total_stock["total_products"],
            "total_stock": total_stock["total_stock"],
            "low_stock_alerts": low_stock_alerts,
            "warehouse_utilization": round(avg_util, 2),
            "total_revenue": round(total_revenue, 2)
        }
    
    def get_stock_by_category(self) -> List[Dict[str, Any]]:
        """Get stock distribution by category"""
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
                    "total_quantity": {"$sum": "$quantity"}
                }
            },
            {
                "$project": {
                    "category": "$_id",
                    "total_quantity": "$total_quantity"
                }
            }
        ]
        
        return list(self.db.inventory.aggregate(pipeline))
    
    def get_top_products_by_revenue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top products by revenue"""
        return list(self.db.products.find(
            {},
            {"_id": 0, "sku": 1, "name": 1, "total_revenue": 1, "total_sales": 1}
        ).sort("total_revenue", -1).limit(limit))
