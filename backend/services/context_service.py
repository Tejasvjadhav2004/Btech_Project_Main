"""
Context Service - Aggregates operational context for LLM orchestration

Collects and summarizes data from across the system for decision-making.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class ContextService:
    """
    Aggregates and summarizes operational system context for orchestration.

    Provides compact, relevant context for LLM reasoning without raw database dumps.
    """

    def __init__(self):
        pass

    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()

    def aggregate_context(self) -> Dict[str, Any]:
        """
        Aggregate comprehensive system-wide operational context.

        Returns:
            Structured context for orchestration
        """
        try:
            context = {
                "timestamp": datetime.utcnow().isoformat(),
                "signals": self._get_signals_summary(),
                "inventory_summary": self._get_inventory_summary(),
                "warehouse_summary": self._get_warehouse_summary(),
                "delivery_summary": self._get_delivery_summary(),
                "forecast_summary": self._get_forecast_summary(),
                "order_summary": self._get_order_summary(),
                "critical_issues": self._get_critical_issues(),
                "recommended_focus": self._get_recommended_focus(),
                "optimization_opportunities": self._get_optimization_opportunities()
            }

            logger.info(f"Context aggregated: {len(context['critical_issues'])} critical issues found")
            return context

        except Exception as e:
            logger.error(f"Error aggregating context: {e}")
            return self._get_empty_context()

    def aggregate_context_for_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate context specifically for processing a signal.

        Args:
            signal: Signal to process

        Returns:
            Context focused on the signal
        """
        try:
            context = self.aggregate_context()

            # Add signal-specific context
            signal_type = signal.get("type")
            entity_id = signal.get("entity_id")
            product_id = signal.get("product_id")

            if signal_type in ["LOW_STOCK", "STOCKOUT"]:
                context["signal_context"] = self._get_inventory_signal_context(
                    entity_id, product_id
                )
            elif signal_type == "DELIVERY_DELAY":
                context["signal_context"] = self._get_delivery_signal_context(entity_id)
            elif signal_type in ["OVER_UTILIZATION", "UNDER_UTILIZATION"]:
                context["signal_context"] = self._get_warehouse_signal_context(entity_id)
            elif signal_type in ["DEMAND_SPIKE", "DEMAND_DROP"]:
                context["signal_context"] = self._get_demand_signal_context()

            context["trigger_signal"] = signal

            return context

        except Exception as e:
            logger.error(f"Error aggregating signal context: {e}")
            return self._get_empty_context()

    def _get_signals_summary(self) -> Dict[str, Any]:
        """Get summarized signals data"""
        try:
            # Get signal counts by type and severity
            pipeline = [
                {"$match": {"status": "active"}},
                {"$group": {
                    "_id": {"type": "$type", "severity": "$severity"},
                    "count": {"$sum": 1}
                }}
            ]

            results = list(self.db.signals.aggregate(pipeline))

            by_type = {}
            by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            total_active = 0

            for item in results:
                signal_type = item["_id"].get("type", "unknown")
                severity = item["_id"].get("severity", "medium")
                count = item.get("count", 0)

                if signal_type not in by_type:
                    by_type[signal_type] = 0
                by_type[signal_type] += count
                by_severity[severity] = by_severity.get(severity, 0) + count
                total_active += count

            # Get top 5 critical signals
            critical_signals = list(self.db.signals.find({
                "status": "active",
                "severity": {"$in": ["critical", "high"]}
            }).sort([("severity", -1), ("created_at", -1)]).limit(5))

            return {
                "total_active": total_active,
                "by_type": by_type,
                "by_severity": by_severity,
                "critical_count": by_severity.get("critical", 0),
                "high_count": by_severity.get("high", 0),
                "top_signals": [
                    {
                        "signal_id": s.get("signal_id"),
                        "type": s.get("type"),
                        "severity": s.get("severity"),
                        "message": s.get("message")[:100] if s.get("message") else None,
                        "entity_id": s.get("entity_id")
                    }
                    for s in critical_signals
                ]
            }

        except Exception as e:
            logger.error(f"Error getting signals summary: {e}")
            return {"total_active": 0, "by_type": {}, "by_severity": {}}

    def _get_inventory_summary(self) -> Dict[str, Any]:
        """Get summarized inventory data"""
        try:
            # Get inventory statistics
            pipeline = [
                {"$group": {
                    "_id": "$location_type",
                    "total_items": {"$sum": "$current_stock"},
                    "locations": {"$addToSet": "$location_id"},
                    "low_stock_count": {
                        "$sum": {"$cond": [
                            {"$lt": ["$current_stock", {"$ifNull": ["$reorder_threshold", 20]}]},
                            1, 0
                        ]}
                    },
                    "out_of_stock_count": {
                        "$sum": {"$cond": [{"$lte": ["$current_stock", 0]}, 1, 0]}
                    },
                    "total_value": {"$sum": {"$multiply": ["$current_stock", {"$ifNull": ["$unit_price", 0]}]}}
                }}
            ]

            results = list(self.db.inventory.aggregate(pipeline))

            summary = {
                "warehouse": {"total_items": 0, "low_stock_count": 0, "out_of_stock_count": 0},
                "store": {"total_items": 0, "low_stock_count": 0, "out_of_stock_count": 0},
                "total_low_stock": 0,
                "total_out_of_stock": 0
            }

            for item in results:
                location_type = item["_id"]
                if location_type in summary:
                    summary[location_type] = {
                        "total_items": item.get("total_items", 0),
                        "low_stock_count": item.get("low_stock_count", 0),
                        "out_of_stock_count": item.get("out_of_stock_count", 0)
                    }
                summary["total_low_stock"] += item.get("low_stock_count", 0)
                summary["total_out_of_stock"] += item.get("out_of_stock_count", 0)

            # Get top 5 low stock items
            low_stock_items = list(self.db.inventory.find({
                "current_stock": {"$lt": 20}
            }).sort("current_stock", 1).limit(5))

            summary["critical_items"] = [
                {
                    "sku": item.get("sku"),
                    "location_id": item.get("location_id"),
                    "current_stock": item.get("current_stock"),
                    "reorder_threshold": item.get("reorder_threshold", 20)
                }
                for item in low_stock_items
            ]

            return summary

        except Exception as e:
            logger.error(f"Error getting inventory summary: {e}")
            return {}

    def _get_warehouse_summary(self) -> Dict[str, Any]:
        """Get summarized warehouse data"""
        try:
            warehouses = list(self.db.warehouses.find({"is_active": True}))

            total_capacity = 0
            total_utilization = 0
            utilization_data = []
            over_utilized = []
            under_utilized = []

            for wh in warehouses:
                capacity = wh.get("capacity", 1)
                current = wh.get("current_utilization", 0)
                util_pct = (current / capacity * 100) if capacity > 0 else 0

                total_capacity += capacity
                total_utilization += current

                utilization_data.append({
                    "warehouse_id": wh.get("warehouse_id"),
                    "name": wh.get("name"),
                    "utilization_percent": round(util_pct, 1),
                    "capacity": capacity,
                    "current": current,
                    "city": wh.get("location", {}).get("city")
                })

                if util_pct > 90:
                    over_utilized.append(wh.get("warehouse_id"))
                elif util_pct < 20:
                    under_utilized.append(wh.get("warehouse_id"))

            avg_utilization = (total_utilization / total_capacity * 100) if total_capacity > 0 else 0

            return {
                "total_warehouses": len(warehouses),
                "total_capacity": total_capacity,
                "total_utilization": total_utilization,
                "avg_utilization_percent": round(avg_utilization, 1),
                "over_utilized_count": len(over_utilized),
                "under_utilized_count": len(under_utilized),
                "over_utilized_ids": over_utilized,
                "under_utilized_ids": under_utilized,
                "utilization_by_warehouse": utilization_data[:10]  # Top 10
            }

        except Exception as e:
            logger.error(f"Error getting warehouse summary: {e}")
            return {}

    def _get_delivery_summary(self) -> Dict[str, Any]:
        """Get summarized delivery data"""
        try:
            # Get delivery counts by status
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "avg_distance": {"$avg": "$distance_km"}
                }}
            ]

            results = list(self.db.deliveries.aggregate(pipeline))

            by_status = {}
            total = 0

            for item in results:
                status = item["_id"]
                count = item.get("count", 0)
                by_status[status] = {
                    "count": count,
                    "avg_distance": round(item.get("avg_distance", 0), 1)
                }
                total += count

            # Get delayed deliveries
            now = datetime.utcnow()
            delayed = list(self.db.deliveries.find({
                "status": "in_transit",
                "estimated_arrival": {"$lt": now}
            }).limit(10))

            delayed_count = len(list(self.db.deliveries.find({
                "status": "in_transit",
                "estimated_arrival": {"$lt": now}
            })))

            return {
                "total_deliveries": total,
                "by_status": by_status,
                "in_transit_count": by_status.get("in_transit", {}).get("count", 0),
                "delayed_count": delayed_count,
                "delayed_deliveries": [
                    {
                        "delivery_id": d.get("delivery_id"),
                        "order_id": d.get("order_id"),
                        "delayed_by_hours": round(
                            (now - d.get("estimated_arrival", now)).total_seconds() / 3600, 1
                        ) if d.get("estimated_arrival") else 0
                    }
                    for d in delayed[:5]
                ]
            }

        except Exception as e:
            logger.error(f"Error getting delivery summary: {e}")
            return {}

    def _get_forecast_summary(self) -> Dict[str, Any]:
        """Get summarized forecast data"""
        try:
            # Get predictions summary
            predictions = list(self.db.predicted_demand.find().limit(50))

            if not predictions:
                return {"available": False, "message": "No forecasts generated"}

            # Analyze predictions
            increasing = []
            decreasing = []
            high_demand = []

            for pred in predictions:
                trend = pred.get("trend", "stable")
                demand_7d = pred.get("predicted_demand_7d", 0)
                sku = pred.get("sku")

                if trend == "increasing":
                    increasing.append(sku)
                elif trend == "decreasing":
                    decreasing.append(sku)

                if demand_7d > 50:
                    high_demand.append({
                        "sku": sku,
                        "predicted_demand_7d": demand_7d,
                        "confidence": pred.get("confidence", 0)
                    })

            # Sort high demand by predicted demand
            high_demand.sort(key=lambda x: x["predicted_demand_7d"], reverse=True)

            return {
                "available": True,
                "total_predictions": len(predictions),
                "increasing_demand_skus": increasing[:10],
                "decreasing_demand_skus": decreasing[:10],
                "high_demand_items": high_demand[:5],
                "avg_confidence": round(
                    sum(p.get("confidence", 0) for p in predictions) / len(predictions), 2
                ) if predictions else 0
            }

        except Exception as e:
            logger.error(f"Error getting forecast summary: {e}")
            return {"available": False}

    def _get_order_summary(self) -> Dict[str, Any]:
        """Get summarized order data"""
        try:
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$total_amount"}
                }}
            ]

            results = list(self.db.orders.aggregate(pipeline))

            by_status = {}
            total = 0
            total_revenue = 0

            for item in results:
                status = item["_id"]
                by_status[status] = {
                    "count": item.get("count", 0),
                    "total_amount": item.get("total_amount", 0)
                }
                total += item.get("count", 0)
                total_revenue += item.get("total_amount", 0)

            # Get pending orders
            pending_count = by_status.get("pending", {}).get("count", 0)

            return {
                "total_orders": total,
                "by_status": by_status,
                "pending_count": pending_count,
                "total_revenue": total_revenue
            }

        except Exception as e:
            logger.error(f"Error getting order summary: {e}")
            return {}

    def _get_critical_issues(self) -> List[Dict[str, Any]]:
        """Identify critical issues requiring attention"""
        issues = []

        try:
            # Stockouts
            stockouts = list(self.db.signals.find({
                "type": "STOCKOUT",
                "status": "active"
            }).limit(5))

            for s in stockouts:
                issues.append({
                    "type": "stockout",
                    "severity": "critical",
                    "description": f"Stockout for {s.get('product_id', 'product')} at {s.get('entity_id')}",
                    "signal_id": s.get("signal_id"),
                    "entity_id": s.get("entity_id"),
                    "product_id": s.get("product_id")
                })

            # Over-utilized warehouses
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            for wh in warehouses:
                capacity = wh.get("capacity", 1)
                current = wh.get("current_utilization", 0)
                util_pct = (current / capacity * 100) if capacity > 0 else 0

                if util_pct > 95:
                    issues.append({
                        "type": "warehouse_over_capacity",
                        "severity": "critical",
                        "description": f"Warehouse {wh.get('warehouse_id')} at {util_pct:.1f}% capacity",
                        "entity_id": wh.get("warehouse_id"),
                        "utilization_percent": round(util_pct, 1)
                    })

            # Delayed deliveries
            now = datetime.utcnow()
            delayed = list(self.db.deliveries.find({
                "status": "in_transit",
                "estimated_arrival": {"$lt": now - timedelta(hours=24)}
            }).limit(3))

            for d in delayed:
                issues.append({
                    "type": "severe_delivery_delay",
                    "severity": "high",
                    "description": f"Delivery {d.get('delivery_id')} delayed by 24+ hours",
                    "entity_id": d.get("delivery_id"),
                    "order_id": d.get("order_id")
                })

            return issues

        except Exception as e:
            logger.error(f"Error getting critical issues: {e}")
            return []

    def _get_recommended_focus(self) -> List[str]:
        """Get recommended focus areas for orchestration"""
        recommendations = []

        try:
            # Check signals
            critical_count = self.db.signals.count_documents({
                "status": "active",
                "severity": "critical"
            })
            if critical_count > 0:
                recommendations.append(f"Address {critical_count} critical signals immediately")

            # Check inventory
            low_stock_count = self.db.inventory.count_documents({
                "current_stock": {"$lt": 20}
            })
            if low_stock_count > 5:
                recommendations.append(f"Review inventory replenishment for {low_stock_count} low-stock items")

            # Check warehouse utilization
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            over_util = [w for w in warehouses if w.get("current_utilization", 0) / w.get("capacity", 1) * 100 > 90]
            if len(over_util) > 0:
                recommendations.append(f"Rebalance load from {len(over_util)} over-utilized warehouses")

            # Check deliveries
            now = datetime.utcnow()
            delayed_count = self.db.deliveries.count_documents({
                "status": "in_transit",
                "estimated_arrival": {"$lt": now}
            })
            if delayed_count > 0:
                recommendations.append(f"Investigate {delayed_count} delayed deliveries")

            if not recommendations:
                recommendations.append("System operating normally - monitor for emerging patterns")

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommended focus: {e}")
            return ["Unable to generate recommendations"]

    def _get_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []

        try:
            # Inventory rebalancing opportunities
            # Find products with imbalanced distribution across warehouses
            pipeline = [
                {"$match": {"location_type": "warehouse"}},
                {"$group": {
                    "_id": "$sku",
                    "warehouses": {"$addToSet": "$location_id"},
                    "total_stock": {"$sum": "$current_stock"},
                    "stock_by_wh": {"$push": {"wh": "$location_id", "stock": "$current_stock"}}
                }}
            ]

            results = list(self.db.inventory.aggregate(pipeline))

            for item in results:
                stock_values = [s["stock"] for s in item.get("stock_by_wh", [])]
                if len(stock_values) >= 2:
                    max_stock = max(stock_values)
                    min_stock = min(stock_values)
                    if max_stock > 0 and max_stock / (min_stock + 1) > 3:
                        opportunities.append({
                            "type": "inventory_rebalance",
                            "sku": item["_id"],
                            "description": f"SKU {item['_id']} has unbalanced distribution",
                            "max_stock": max_stock,
                            "min_stock": min_stock,
                            "priority": "medium"
                        })

            # Warehouse load balancing
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            if warehouses:
                utils = [(w.get("current_utilization", 0) / w.get("capacity", 1) * 100) for w in warehouses]
                if max(utils) - min(utils) > 40:
                    opportunities.append({
                        "type": "warehouse_load_balance",
                        "description": "Significant utilization imbalance between warehouses",
                        "range": f"{min(utils):.1f}% - {max(utils):.1f}%",
                        "priority": "low"
                    })

            return opportunities[:5]  # Top 5 opportunities

        except Exception as e:
            logger.error(f"Error getting optimization opportunities: {e}")
            return []

    def _get_inventory_signal_context(
        self,
        location_id: str,
        product_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get context specific to inventory signals"""
        context = {}

        try:
            if product_id:
                # Get all inventory for this product
                inv_list = list(self.db.inventory.find({"sku": product_id}))
                context["product_inventory"] = [
                    {
                        "location_id": i.get("location_id"),
                        "location_type": i.get("location_type"),
                        "current_stock": i.get("current_stock"),
                        "reserved_stock": i.get("reserved_stock"),
                        "available_stock": i.get("current_stock", 0) - i.get("reserved_stock", 0),
                        "reorder_threshold": i.get("reorder_threshold"),
                        "reorder_quantity": i.get("reorder_quantity")
                    }
                    for i in inv_list
                ]

                # Get product info
                product = self.db.products.find_one({"sku": product_id})
                if product:
                    context["product_info"] = {
                        "name": product.get("name"),
                        "category": product.get("category"),
                        "brand": product.get("brand"),
                        "price": product.get("current_price")
                    }

                # Get suppliers
                suppliers = list(self.db.suppliers.find({"products": product_id}))
                context["available_suppliers"] = [
                    {"supplier_id": s.get("supplier_id"), "name": s.get("name")}
                    for s in suppliers
                ]

        except Exception as e:
            logger.error(f"Error getting inventory signal context: {e}")

        return context

    def _get_delivery_signal_context(self, delivery_id: str) -> Dict[str, Any]:
        """Get context specific to delivery signals"""
        context = {}

        try:
            delivery = self.db.deliveries.find_one({"delivery_id": delivery_id})
            if delivery:
                context["delivery_details"] = {
                    "order_id": delivery.get("order_id"),
                    "warehouse_id": delivery.get("warehouse_id"),
                    "store_id": delivery.get("store_id"),
                    "transport_mode": delivery.get("transport_mode"),
                    "distance_km": delivery.get("distance_km"),
                    "status": delivery.get("status"),
                    "estimated_arrival": delivery.get("estimated_arrival", {}).isoformat() if delivery.get("estimated_arrival") else None,
                    "actual_arrival": delivery.get("actual_arrival", {}).isoformat() if delivery.get("actual_arrival") else None
                }

                # Get order info
                if delivery.get("order_id"):
                    order = self.db.orders.find_one({"order_id": delivery.get("order_id")})
                    if order:
                        context["order_details"] = {
                            "priority": order.get("priority"),
                            "status": order.get("status"),
                            "items": order.get("items")
                        }

        except Exception as e:
            logger.error(f"Error getting delivery signal context: {e}")

        return context

    def _get_warehouse_signal_context(self, warehouse_id: str) -> Dict[str, Any]:
        """Get context specific to warehouse signals"""
        context = {}

        try:
            warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
            if warehouse:
                capacity = warehouse.get("capacity", 1)
                current = warehouse.get("current_utilization", 0)

                context["warehouse_details"] = {
                    "name": warehouse.get("name"),
                    "city": warehouse.get("location", {}).get("city"),
                    "capacity": capacity,
                    "current_utilization": current,
                    "utilization_percent": round((current / capacity * 100) if capacity > 0 else 0, 1),
                    "is_active": warehouse.get("is_active")
                }

                # Get inventory at this warehouse
                inv = list(self.db.inventory.find({
                    "location_id": warehouse_id,
                    "location_type": "warehouse"
                }).limit(20))

                context["top_inventory"] = [
                    {
                        "sku": i.get("sku"),
                        "current_stock": i.get("current_stock"),
                        "reserved_stock": i.get("reserved_stock")
                    }
                    for i in sorted(inv, key=lambda x: x.get("current_stock", 0), reverse=True)[:10]
                ]

        except Exception as e:
            logger.error(f"Error getting warehouse signal context: {e}")

        return context

    def _get_demand_signal_context(self) -> Dict[str, Any]:
        """Get context specific to demand signals"""
        context = {}

        try:
            # Get recent order patterns
            now = datetime.utcnow()
            recent_orders = list(self.db.orders.find({
                "created_at": {"$gte": now - timedelta(hours=24)}
            }))

            # Group by SKU
            sku_demand = {}
            for order in recent_orders:
                for item in order.get("items", []):
                    sku = item.get("sku")
                    if sku not in sku_demand:
                        sku_demand[sku] = 0
                    sku_demand[sku] += item.get("quantity", 0)

            # Sort by demand
            sorted_demand = sorted(sku_demand.items(), key=lambda x: x[1], reverse=True)

            context["top_demand_24h"] = [
                {"sku": sku, "quantity": qty}
                for sku, qty in sorted_demand[:10]
            ]

            # Get forecasts
            predictions = list(self.db.predicted_demand.find().limit(20))
            context["forecast_trends"] = [
                {
                    "sku": p.get("sku"),
                    "trend": p.get("trend"),
                    "predicted_demand_7d": p.get("predicted_demand_7d")
                }
                for p in predictions
                if p.get("trend") != "stable"
            ]

        except Exception as e:
            logger.error(f"Error getting demand signal context: {e}")

        return context

    def _get_empty_context(self) -> Dict[str, Any]:
        """Return empty context structure"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "signals": {},
            "inventory_summary": {},
            "warehouse_summary": {},
            "delivery_summary": {},
            "forecast_summary": {},
            "order_summary": {},
            "critical_issues": [],
            "recommended_focus": [],
            "optimization_opportunities": []
        }


# Global instance
context_service = ContextService()
