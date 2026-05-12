"""
Optimization Agent - Handles warehouse, inventory, and route optimization

Part of the multi-agent orchestration system.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from db.connection import mongodb
import logging
import math

logger = logging.getLogger(__name__)


class OptimizationAgent:
    """
    Agent responsible for optimization decisions.

    Capabilities:
    - Warehouse selection optimization
    - Inventory balancing across warehouses
    - Route optimization
    - Load balancing recommendations
    """

    AGENT_NAME = "optimization_agent"
    AGENT_TYPE = "optimization"

    def __init__(self):
        pass

    @property
    def db(self):
        return mongodb.get_database()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and generate optimization recommendations.

        Args:
            context: Aggregated operational context

        Returns:
            Optimization agent output with recommendations
        """
        try:
            logger.info("Optimization Agent processing context")

            # Analyze warehouse utilization
            warehouse_optimization = self._analyze_warehouse_optimization(
                context.get("warehouse_summary", {})
            )

            # Analyze inventory balancing opportunities
            inventory_balancing = self._analyze_inventory_balancing(context)

            # Analyze route optimization opportunities
            route_optimization = self._analyze_route_optimization(context)

            # Calculate efficiency metrics
            efficiency_metrics = self._calculate_efficiency_metrics(context)

            # Generate optimization plan
            optimization_plan = self._generate_optimization_plan(
                warehouse_optimization,
                inventory_balancing,
                route_optimization
            )

            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "timestamp": datetime.utcnow().isoformat(),
                "warehouse_optimization": warehouse_optimization,
                "inventory_balancing": inventory_balancing,
                "route_optimization": route_optimization,
                "efficiency_metrics": efficiency_metrics,
                "optimization_plan": optimization_plan,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Optimization Agent error: {e}")
            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "status": "error",
                "error": str(e)
            }

    def _analyze_warehouse_optimization(
        self,
        warehouse_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze warehouse utilization and optimization opportunities"""
        analysis = {
            "over_utilized": [],
            "under_utilized": [],
            "balanced": [],
            "load_balance_needed": False,
            "recommendations": []
        }

        try:
            utilization_data = warehouse_summary.get("utilization_by_warehouse", [])

            for wh in utilization_data:
                util_pct = wh.get("utilization_percent", 0)
                wh_data = {
                    "warehouse_id": wh.get("warehouse_id"),
                    "name": wh.get("name"),
                    "utilization_percent": util_pct,
                    "city": wh.get("city")
                }

                if util_pct > 90:
                    analysis["over_utilized"].append(wh_data)
                elif util_pct < 30:
                    analysis["under_utilized"].append(wh_data)
                else:
                    analysis["balanced"].append(wh_data)

            # Check if load balancing is needed
            if analysis["over_utilized"] and analysis["under_utilized"]:
                analysis["load_balance_needed"] = True
                analysis["recommendations"].append(
                    f"Transfer inventory from {analysis['over_utilized'][0]['warehouse_id']} "
                    f"to {analysis['under_utilized'][0]['warehouse_id']}"
                )

            # Add specific recommendations
            for wh in analysis["over_utilized"]:
                analysis["recommendations"].append(
                    f"Warehouse {wh['warehouse_id']} at {wh['utilization_percent']:.1f}% - consider redistribution"
                )

        except Exception as e:
            logger.error(f"Error analyzing warehouse optimization: {e}")

        return analysis

    def _analyze_inventory_balancing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inventory balancing opportunities"""
        balancing = {
            "opportunities": [],
            "total_imbalance_score": 0,
            "recommended_transfers": []
        }

        try:
            # Find SKUs with imbalanced distribution
            pipeline = [
                {"$match": {"location_type": "warehouse"}},
                {"$group": {
                    "_id": "$sku",
                    "warehouses": {"$push": {
                        "wh": "$location_id",
                        "stock": "$current_stock",
                        "reserved": "$reserved_stock"
                    }},
                    "total_stock": {"$sum": "$current_stock"},
                    "count": {"$sum": 1}
                }},
                {"$match": {"count": {"$gte": 2}}}
            ]

            results = list(self.db.inventory.aggregate(pipeline))

            for item in results:
                sku = item["_id"]
                warehouses = item.get("warehouses", [])

                # Calculate imbalance
                stocks = [w["stock"] for w in warehouses]
                if not stocks:
                    continue

                max_stock = max(stocks)
                min_stock = min(stocks)
                avg_stock = sum(stocks) / len(stocks)

                # Calculate coefficient of variation
                if avg_stock > 0:
                    std_dev = math.sqrt(sum((s - avg_stock) ** 2 for s in stocks) / len(stocks))
                    cv = std_dev / avg_stock

                    # High coefficient of variation indicates imbalance
                    if cv > 0.5 and max_stock > 50:
                        source_wh = max(warehouses, key=lambda x: x["stock"])
                        target_wh = min(warehouses, key=lambda x: x["stock"])

                        transfer_qty = int((max_stock - min_stock) / 2)

                        if transfer_qty > 10:
                            balancing["opportunities"].append({
                                "sku": sku,
                                "imbalance_score": round(cv, 2),
                                "source_warehouse": source_wh["wh"],
                                "target_warehouse": target_wh["wh"],
                                "source_stock": source_wh["stock"],
                                "target_stock": target_wh["stock"],
                                "suggested_transfer_qty": transfer_qty
                            })

            # Sort by imbalance score
            balancing["opportunities"].sort(
                key=lambda x: x["imbalance_score"],
                reverse=True
            )

            # Calculate total imbalance score
            balancing["total_imbalance_score"] = sum(
                o["imbalance_score"] for o in balancing["opportunities"]
            )

            # Generate recommended transfers (top 5)
            for opp in balancing["opportunities"][:5]:
                balancing["recommended_transfers"].append({
                    "action": "transfer_inventory",
                    "sku": opp["sku"],
                    "source_warehouse": opp["source_warehouse"],
                    "target_warehouse": opp["target_warehouse"],
                    "quantity": opp["suggested_transfer_qty"]
                })

        except Exception as e:
            logger.error(f"Error analyzing inventory balancing: {e}")

        return balancing

    def _analyze_route_optimization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze route optimization opportunities"""
        optimization = {
            "improvements": [],
            "potential_savings": {
                "distance_km": 0,
                "time_hours": 0
            }
        }

        try:
            # Analyze pending deliveries
            pending_deliveries = list(self.db.deliveries.find({
                "status": "pending"
            }).limit(20))

            # Group by destination
            by_destination = {}
            for delivery in pending_deliveries:
                store_id = delivery.get("store_id")
                if store_id not in by_destination:
                    by_destination[store_id] = []
                by_destination[store_id].append(delivery)

            # Identify consolidation opportunities
            for store_id, deliveries in by_destination.items():
                if len(deliveries) > 1:
                    total_distance = sum(d.get("distance_km", 0) for d in deliveries)

                    optimization["improvements"].append({
                        "type": "consolidation",
                        "store_id": store_id,
                        "delivery_count": len(deliveries),
                        "current_total_distance": round(total_distance, 1),
                        "potential_savings_km": round(total_distance * 0.3, 1),
                        "description": f"Consolidate {len(deliveries)} deliveries to {store_id}"
                    })

                    optimization["potential_savings"]["distance_km"] += total_distance * 0.3

            # Analyze in-transit deliveries for rerouting potential
            in_transit = list(self.db.deliveries.find({
                "status": "in_transit"
            }).limit(10))

            for delivery in in_transit:
                distance = delivery.get("distance_km", 0)
                transport = delivery.get("transport_mode", "truck")
                warehouse_id = delivery.get("warehouse_id")
                store_id = delivery.get("store_id")

                # Check if there's a closer warehouse
                warehouse = self.db.warehouses.find_one({"warehouse_id": warehouse_id})
                store = self.db.stores.find_one({"store_id": store_id})

                if warehouse and store:
                    # Simple distance calculation
                    wh_coords = warehouse.get("location", {}).get("coordinates", {})
                    store_coords = store.get("location", {}).get("coordinates", {})

                    # Find alternative warehouses
                    other_warehouses = list(self.db.warehouses.find({
                        "warehouse_id": {"$ne": warehouse_id},
                        "is_active": True
                    }))

                    for alt_wh in other_warehouses:
                        alt_coords = alt_wh.get("location", {}).get("coordinates", {})
                        # Simplified distance check (in reality would use proper geospatial query)
                        if distance > 500 and transport == "truck":
                            optimization["improvements"].append({
                                "type": "reroute",
                                "delivery_id": delivery.get("delivery_id"),
                                "current_transport": transport,
                                "suggested_transport": "express",
                                "reason": "Long distance delivery could benefit from faster transport"
                            })
                            break

        except Exception as e:
            logger.error(f"Error analyzing route optimization: {e}")

        return optimization

    def _calculate_efficiency_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate system efficiency metrics"""
        metrics = {
            "warehouse_efficiency": 0,
            "inventory_efficiency": 0,
            "delivery_efficiency": 0,
            "overall_score": 0
        }

        try:
            # Warehouse efficiency (based on utilization balance)
            wh_summary = context.get("warehouse_summary", {})
            avg_util = wh_summary.get("avg_utilization_percent", 0)

            # Ideal is 70-80% utilization
            if 60 <= avg_util <= 85:
                metrics["warehouse_efficiency"] = 0.9
            elif 50 <= avg_util <= 95:
                metrics["warehouse_efficiency"] = 0.7
            else:
                metrics["warehouse_efficiency"] = 0.5

            # Inventory efficiency (based on stockout rate)
            inv_summary = context.get("inventory_summary", {})
            low_stock = inv_summary.get("total_low_stock", 0)
            out_of_stock = inv_summary.get("total_out_of_stock", 0)

            total_items = inv_summary.get("warehouse", {}).get("total_items", 1) + \
                          inv_summary.get("store", {}).get("total_items", 1)

            if total_items > 0:
                stockout_rate = out_of_stock / total_items
                if stockout_rate < 0.02:
                    metrics["inventory_efficiency"] = 0.9
                elif stockout_rate < 0.05:
                    metrics["inventory_efficiency"] = 0.7
                else:
                    metrics["inventory_efficiency"] = 0.5

            # Delivery efficiency (based on delay rate)
            del_summary = context.get("delivery_summary", {})
            in_transit = del_summary.get("in_transit_count", 0)
            delayed = del_summary.get("delayed_count", 0)

            if in_transit > 0:
                delay_rate = delayed / in_transit
                if delay_rate < 0.1:
                    metrics["delivery_efficiency"] = 0.9
                elif delay_rate < 0.2:
                    metrics["delivery_efficiency"] = 0.7
                else:
                    metrics["delivery_efficiency"] = 0.5
            else:
                metrics["delivery_efficiency"] = 0.8  # Default if no deliveries

            # Overall score
            metrics["overall_score"] = round(
                (metrics["warehouse_efficiency"] +
                 metrics["inventory_efficiency"] +
                 metrics["delivery_efficiency"]) / 3,
                2
            )

        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")

        return metrics

    def _generate_optimization_plan(
        self,
        warehouse_opt: Dict[str, Any],
        inv_balancing: Dict[str, Any],
        route_opt: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized optimization plan"""
        plan = []

        # Add inventory balancing actions (high priority)
        for transfer in inv_balancing.get("recommended_transfers", [])[:3]:
            plan.append({
                "priority": "high",
                "action": transfer["action"],
                "details": transfer,
                "reason": "Inventory imbalance detected",
                "expected_benefit": "Improved stock availability and warehouse balance"
            })

        # Add warehouse load balancing (medium priority)
        if warehouse_opt.get("load_balance_needed"):
            for wh in warehouse_opt.get("over_utilized", [])[:2]:
                plan.append({
                    "priority": "medium",
                    "action": "rebalance_inventory",
                    "source_warehouse": wh["warehouse_id"],
                    "reason": f"Warehouse at {wh['utilization_percent']:.1f}% capacity",
                    "expected_benefit": "Reduced warehouse congestion and improved throughput"
                })

        # Add route improvements (low priority)
        for improvement in route_opt.get("improvements", [])[:3]:
            plan.append({
                "priority": "low",
                "action": improvement["type"],
                "details": improvement,
                "reason": "Route optimization opportunity",
                "expected_benefit": f"Save {improvement.get('potential_savings_km', 0):.1f} km"
            })

        return plan

    def optimize_warehouse_selection(
        self,
        sku: str,
        store_id: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Optimize warehouse selection for an order.

        Args:
            sku: Product SKU
            store_id: Destination store
            quantity: Required quantity

        Returns:
            Optimal warehouse recommendation
        """
        try:
            from services.warehouse_service import WarehouseService

            warehouse_service = WarehouseService()
            decision = warehouse_service.select_warehouse(sku, store_id, quantity)

            return {
                "recommended_warehouse": decision.get("selected_warehouse", {}).get("warehouse_id"),
                "alternatives": [
                    w.get("warehouse_id") for w in decision.get("alternatives", [])[:3]
                ],
                "distance_km": decision.get("selected_warehouse", {}).get("distance_km"),
                "stock_available": decision.get("selected_warehouse", {}).get("available_stock"),
                "reasoning": f"Selected based on distance ({decision.get('selected_warehouse', {}).get('distance_km')}km) and stock availability"
            }

        except Exception as e:
            logger.error(f"Error optimizing warehouse selection: {e}")
            return {"error": str(e)}


# Global instance
optimization_agent = OptimizationAgent()
