"""
Context Aggregation Service

Aggregates operational context from multiple sources for orchestration decisions.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from db.connection import mongodb
from orchestration.models.schemas import OperationalContext
import logging

logger = logging.getLogger(__name__)


class ContextService:
    """
    Aggregates operational context from inventory, warehouses, deliveries,
    predictions, and signals for orchestration decision-making.
    """

    def __init__(self):
        pass

    @property
    def db(self):
        return mongodb.get_database()

    def aggregate_context_for_signal(self, signal: Dict[str, Any]) -> OperationalContext:
        """
        Aggregate comprehensive operational context for a signal.

        Args:
            signal: Signal document from signals collection

        Returns:
            OperationalContext with aggregated data
        """
        signal_id = signal.get("signal_id")
        signal_type = signal.get("type")
        signal_severity = signal.get("severity", "medium")
        details = signal.get("details", {})

        # Extract entity information
        sku = details.get("sku") or signal.get("product_id")
        warehouse_id = signal.get("entity_id") if signal.get("entity_type") == "warehouse" else None
        store_id = signal.get("entity_id") if signal.get("entity_type") == "store" else None

        # Build context
        context = OperationalContext(
            signal_id=signal_id,
            signal_type=signal_type,
            signal_severity=signal_severity,
            sku=sku,
            warehouse_id=warehouse_id,
            store_id=store_id,
            details=details
        )

        # Enrich with inventory context
        if sku:
            self._enrich_inventory_context(context, sku, warehouse_id or store_id)

        # Enrich with warehouse context
        if warehouse_id:
            self._enrich_warehouse_context(context, warehouse_id, sku)

        # Enrich with prediction context
        if sku and (warehouse_id or store_id):
            location_id = warehouse_id or store_id
            self._enrich_prediction_context(context, sku, location_id)

        # Enrich with order context
        self._enrich_order_context(context, sku, warehouse_id, store_id)

        # Enrich with delivery context
        self._enrich_delivery_context(context, warehouse_id, store_id)

        logger.info(f"Context aggregated for signal {signal_id}: {signal_type}")
        return context

    def _enrich_inventory_context(
        self,
        context: OperationalContext,
        sku: str,
        location_id: Optional[str]
    ):
        """Enrich context with inventory data"""
        try:
            if not location_id:
                return

            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": location_id
            })

            if inventory:
                context.current_stock = inventory.get("current_stock", inventory.get("quantity", 0))
                context.reserved_stock = inventory.get("reserved_stock", 0)
                context.available_stock = context.current_stock - context.reserved_stock
                context.lead_time_days = inventory.get("lead_time_days", 7)

        except Exception as e:
            logger.warning(f"Failed to enrich inventory context: {e}")

    def _enrich_warehouse_context(
        self,
        context: OperationalContext,
        warehouse_id: str,
        sku: Optional[str]
    ):
        """Enrich context with warehouse data"""
        try:
            warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})

            if warehouse:
                capacity = warehouse.get("capacity", 1)
                current_util = warehouse.get("current_utilization", 0)
                context.warehouse_capacity = capacity
                context.warehouse_utilization = (current_util / capacity * 100) if capacity > 0 else 0

            # Find nearby warehouses as alternatives
            context.nearby_warehouses = self._find_nearby_warehouses(warehouse_id, sku)

        except Exception as e:
            logger.warning(f"Failed to enrich warehouse context: {e}")

    def _find_nearby_warehouses(
        self,
        warehouse_id: str,
        sku: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Find nearby warehouses with available stock"""
        try:
            # Get current warehouse location
            current_wh = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
            if not current_wh:
                return []

            # Get other active warehouses
            other_warehouses = list(self.db.warehouses.find({
                "warehouse_id": {"$ne": warehouse_id},
                "is_active": True
            }))

            nearby = []
            for wh in other_warehouses[:5]:  # Limit to 5 alternatives
                # Check stock if SKU is provided
                available_stock = 0
                if sku:
                    inv = self.db.inventory.find_one({
                        "sku": sku,
                        "location_id": wh["warehouse_id"]
                    })
                    if inv:
                        available_stock = inv.get("quantity", 0) - inv.get("reserved_stock", 0)
                    if available_stock <= 0:
                        continue

                capacity = wh.get("capacity", 1)
                current = wh.get("current_utilization", 0)
                utilization = (current / capacity * 100) if capacity > 0 else 0

                nearby.append({
                    "warehouse_id": wh["warehouse_id"],
                    "name": wh.get("name"),
                    "city": wh.get("location", {}).get("city"),
                    "available_stock": available_stock,
                    "utilization_percent": round(utilization, 2)
                })

            return nearby

        except Exception as e:
            logger.warning(f"Failed to find nearby warehouses: {e}")
            return []

    def _enrich_prediction_context(
        self,
        context: OperationalContext,
        sku: str,
        location_id: str
    ):
        """Enrich context with ML prediction data"""
        try:
            # Get demand prediction
            prediction = self.db.predicted_demand.find_one({
                "sku": sku,
                "store_id": location_id
            })

            if prediction:
                context.predicted_demand = prediction.get("predicted_demand_7d")

            # Get predictive risks
            stockout_risk = self.db.signals.find_one({
                "type": "PREDICTED_STOCKOUT",
                "product_id": sku,
                "entity_id": location_id,
                "status": "active"
            }, {"details": 1})

            if stockout_risk:
                context.stockout_risk = stockout_risk.get("details", {}).get("probability")

            delay_risk = self.db.signals.find_one({
                "type": "PREDICTED_DELAY",
                "status": "active"
            }, {"details": 1})

            if delay_risk:
                context.delay_risk = delay_risk.get("details", {}).get("probability")

        except Exception as e:
            logger.warning(f"Failed to enrich prediction context: {e}")

    def _enrich_order_context(
        self,
        context: OperationalContext,
        sku: Optional[str],
        warehouse_id: Optional[str],
        store_id: Optional[str]
    ):
        """Enrich context with order data"""
        try:
            # Count pending orders
            query = {"status": {"$in": ["pending", "allocated"]}}
            if sku:
                query["items.sku"] = sku
            if store_id:
                query["store_id"] = store_id

            context.pending_orders = self.db.orders.count_documents(query)

            # Count priority orders
            priority_query = dict(query)
            priority_query["priority"] = "high"
            context.priority_orders = self.db.orders.count_documents(priority_query)

        except Exception as e:
            logger.warning(f"Failed to enrich order context: {e}")

    def _enrich_delivery_context(
        self,
        context: OperationalContext,
        warehouse_id: Optional[str],
        store_id: Optional[str]
    ):
        """Enrich context with delivery data"""
        try:
            # Count active deliveries
            query = {"status": {"$in": ["pending", "in_transit"]}}
            if warehouse_id:
                query["warehouse_id"] = warehouse_id
            if store_id:
                query["store_id"] = store_id

            context.active_deliveries = self.db.deliveries.count_documents(query)

            # Count delayed deliveries
            delayed_query = {
                "status": "in_transit",
                "estimated_arrival": {"$lt": datetime.utcnow()}
            }
            context.delayed_deliveries = self.db.deliveries.count_documents(delayed_query)

        except Exception as e:
            logger.warning(f"Failed to enrich delivery context: {e}")

    def get_system_wide_context(self) -> Dict[str, Any]:
        """
        Get system-wide operational context for strategic orchestration.
        """
        try:
            context = {
                "timestamp": datetime.utcnow().isoformat(),
                "inventory": self._get_inventory_summary(),
                "warehouses": self._get_warehouse_summary(),
                "orders": self._get_order_summary(),
                "deliveries": self._get_delivery_summary(),
                "signals": self._get_signal_summary(),
                "predictions": self._get_prediction_summary()
            }
            return context

        except Exception as e:
            logger.error(f"Failed to get system-wide context: {e}")
            return {}

    def _get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        try:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_items": {"$sum": 1},
                    "total_stock": {"$sum": "$quantity"},
                    "low_stock_count": {
                        "$sum": {"$cond": [{"$lt": ["$quantity", 20]}, 1, 0]}
                    }
                }}
            ]
            result = list(self.db.inventory.aggregate(pipeline))
            return result[0] if result else {}
        except Exception:
            return {}

    def _get_warehouse_summary(self) -> Dict[str, Any]:
        """Get warehouse summary statistics"""
        try:
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            total_capacity = sum(w.get("capacity", 0) for w in warehouses)
            total_utilization = sum(w.get("current_utilization", 0) for w in warehouses)

            return {
                "total_warehouses": len(warehouses),
                "total_capacity": total_capacity,
                "total_utilization": total_utilization,
                "avg_utilization_percent": (total_utilization / total_capacity * 100) if total_capacity > 0 else 0
            }
        except Exception:
            return {}

    def _get_order_summary(self) -> Dict[str, Any]:
        """Get order summary statistics"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            return {item["_id"]: item["count"] for item in self.db.orders.aggregate(pipeline)}
        except Exception:
            return {}

    def _get_delivery_summary(self) -> Dict[str, Any]:
        """Get delivery summary statistics"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            return {item["_id"]: item["count"] for item in self.db.deliveries.aggregate(pipeline)}
        except Exception:
            return {}

    def _get_signal_summary(self) -> Dict[str, Any]:
        """Get signal summary statistics"""
        try:
            return {
                "active": self.db.signals.count_documents({"status": "active"}),
                "critical": self.db.signals.count_documents({"status": "active", "severity": "critical"}),
                "high": self.db.signals.count_documents({"status": "active", "severity": "high"})
            }
        except Exception:
            return {}

    def _get_prediction_summary(self) -> Dict[str, Any]:
        """Get prediction summary statistics"""
        try:
            predictions = list(self.db.predicted_demand.find({
                "generated_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            }))
            return {
                "total_predictions": len(predictions),
                "increasing_trend": len([p for p in predictions if p.get("trend") == "increasing"]),
                "decreasing_trend": len([p for p in predictions if p.get("trend") == "decreasing"])
            }
        except Exception:
            return {}


# Global instance
context_service = ContextService()
