"""
Forecasting Agent - Handles demand prediction and delay risk forecasting

Part of the multi-agent orchestration system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class ForecastingAgent:
    """
    Agent responsible for demand forecasting and delay prediction.

    Capabilities:
    - Generate demand forecasts using ML models
    - Predict delay risks
    - Identify stockout risks
    - Provide forecast-based recommendations
    """

    AGENT_NAME = "forecasting_agent"
    AGENT_TYPE = "forecasting"

    def __init__(self):
        self.model_loaded = False

    @property
    def db(self):
        return mongodb.get_database()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and generate forecast-based insights.

        Args:
            context: Aggregated operational context

        Returns:
            Forecasting agent output with predictions and risks
        """
        try:
            logger.info("Forecasting Agent processing context")

            # Analyze existing forecasts
            forecast_analysis = self._analyze_forecasts(context.get("forecast_summary", {}))

            # Identify stockout risks
            stockout_risks = self._identify_stockout_risks(context)

            # Identify delay risks
            delay_risks = self._identify_delay_risks(context)

            # Calculate inventory coverage
            coverage_analysis = self._analyze_inventory_coverage(context)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                forecast_analysis, stockout_risks, delay_risks, coverage_analysis
            )

            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "timestamp": datetime.utcnow().isoformat(),
                "forecast_analysis": forecast_analysis,
                "stockout_risks": stockout_risks,
                "delay_risks": delay_risks,
                "inventory_coverage": coverage_analysis,
                "recommendations": recommendations,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Forecasting Agent error: {e}")
            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "status": "error",
                "error": str(e)
            }

    def _analyze_forecasts(self, forecast_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze forecast data from context"""
        analysis = {
            "forecasts_available": forecast_summary.get("available", False),
            "total_predictions": forecast_summary.get("total_predictions", 0),
            "avg_confidence": forecast_summary.get("avg_confidence", 0),
            "trend_summary": {
                "increasing": len(forecast_summary.get("increasing_demand_skus", [])),
                "decreasing": len(forecast_summary.get("decreasing_demand_skus", []))
            },
            "high_demand_items": forecast_summary.get("high_demand_items", [])[:5],
            "attention_needed": []
        }

        # Identify items that need attention
        increasing = forecast_summary.get("increasing_demand_skus", [])
        if len(increasing) > 3:
            analysis["attention_needed"].append({
                "type": "demand_increase",
                "description": f"{len(increasing)} SKUs showing increasing demand trend",
                "action": "Review inventory levels for these SKUs"
            })

        # Check confidence levels
        if analysis["avg_confidence"] < 0.7:
            analysis["attention_needed"].append({
                "type": "low_forecast_confidence",
                "description": f"Average forecast confidence is {analysis['avg_confidence']:.0%}",
                "action": "Consider retraining models or gathering more data"
            })

        return analysis

    def _identify_stockout_risks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify items at risk of stockout"""
        risks = []

        try:
            # Get predictions with increasing demand
            forecasts = list(self.db.predicted_demand.find({
                "trend": "increasing"
            }).limit(20))

            for forecast in forecasts:
                sku = forecast.get("sku")
                store_id = forecast.get("store_id")

                # Find corresponding inventory
                inv = self.db.inventory.find_one({
                    "sku": sku,
                    "location_id": store_id
                })

                if inv:
                    current_stock = inv.get("current_stock", 0)
                    predicted_demand = forecast.get("predicted_demand_7d", 0)

                    # Calculate coverage days
                    daily_demand = predicted_demand / 7 if predicted_demand > 0 else 0
                    coverage_days = current_stock / daily_demand if daily_demand > 0 else 999

                    if coverage_days < 7:
                        risks.append({
                            "sku": sku,
                            "store_id": store_id,
                            "current_stock": current_stock,
                            "predicted_daily_demand": round(daily_demand, 1),
                            "coverage_days": round(coverage_days, 1),
                            "risk_level": "high" if coverage_days < 3 else "medium",
                            "recommended_action": "replenish_inventory"
                        })

        except Exception as e:
            logger.error(f"Error identifying stockout risks: {e}")

        return sorted(risks, key=lambda x: x["coverage_days"])[:10]

    def _identify_delay_risks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify deliveries at risk of delay"""
        risks = []

        try:
            # Get in-transit deliveries
            in_transit = list(self.db.deliveries.find({
                "status": "in_transit"
            }).limit(20))

            now = datetime.utcnow()

            for delivery in in_transit:
                eta = delivery.get("estimated_arrival")
                if eta:
                    hours_until_delivery = (eta - now).total_seconds() / 3600

                    # Simple risk assessment based on distance and time
                    distance = delivery.get("distance_km", 0)
                    transport_mode = delivery.get("transport_mode", "truck")

                    # Expected speeds
                    speeds = {"truck": 50, "air": 500, "express": 100, "rail": 80}
                    speed = speeds.get(transport_mode, 50)

                    expected_hours = distance / speed if speed > 0 else 0

                    # Check if behind schedule
                    if hours_until_delivery < expected_hours:
                        delay_risk = (expected_hours - hours_until_delivery) / expected_hours

                        risks.append({
                            "delivery_id": delivery.get("delivery_id"),
                            "order_id": delivery.get("order_id"),
                            "transport_mode": transport_mode,
                            "distance_km": distance,
                            "hours_until_eta": round(hours_until_delivery, 1),
                            "expected_hours": round(expected_hours, 1),
                            "delay_risk_score": round(delay_risk, 2),
                            "risk_level": "high" if delay_risk > 0.5 else "medium",
                            "recommended_action": "reroute_delivery" if delay_risk > 0.5 else "monitor"
                        })

        except Exception as e:
            logger.error(f"Error identifying delay risks: {e}")

        return sorted(risks, key=lambda x: x["delay_risk_score"], reverse=True)[:10]

    def _analyze_inventory_coverage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inventory coverage against forecasted demand"""
        analysis = {
            "under_supplied": [],
            "over_supplied": [],
            "balanced": []
        }

        try:
            # Get high demand forecasts
            high_demand = list(self.db.predicted_demand.find({
                "predicted_demand_7d": {"$gt": 30}
            }).limit(30))

            for forecast in high_demand:
                sku = forecast.get("sku")
                predicted_demand = forecast.get("predicted_demand_7d", 0)

                # Get total inventory for SKU
                inv_records = list(self.db.inventory.find({"sku": sku}))
                total_stock = sum(i.get("current_stock", 0) for i in inv_records)
                reserved = sum(i.get("reserved_stock", 0) for i in inv_records)
                available = total_stock - reserved

                coverage_ratio = available / predicted_demand if predicted_demand > 0 else 999

                item = {
                    "sku": sku,
                    "total_stock": total_stock,
                    "available_stock": available,
                    "predicted_demand": predicted_demand,
                    "coverage_ratio": round(coverage_ratio, 2)
                }

                if coverage_ratio < 1.5:
                    analysis["under_supplied"].append(item)
                elif coverage_ratio > 3:
                    analysis["over_supplied"].append(item)
                else:
                    analysis["balanced"].append(item)

        except Exception as e:
            logger.error(f"Error analyzing inventory coverage: {e}")

        return analysis

    def _generate_recommendations(
        self,
        forecast_analysis: Dict[str, Any],
        stockout_risks: List[Dict[str, Any]],
        delay_risks: List[Dict[str, Any]],
        coverage_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate forecasting-based recommendations"""
        recommendations = []

        # Stockout risks
        high_risk_stockouts = [r for r in stockout_risks if r["risk_level"] == "high"]
        if high_risk_stockouts:
            recommendations.append(
                f"Urgent: {len(high_risk_stockouts)} items at high stockout risk - immediate replenishment needed"
            )

        # Delay risks
        high_risk_delays = [r for r in delay_risks if r["risk_level"] == "high"]
        if high_risk_delays:
            recommendations.append(
                f"Review {len(high_risk_delays)} high-risk deliveries for potential rerouting"
            )

        # Coverage analysis
        under_supplied = coverage_analysis.get("under_supplied", [])
        if under_supplied:
            recommendations.append(
                f"Plan replenishment for {len(under_supplied)} under-supplied SKUs"
            )

        # Trend insights
        trend = forecast_analysis.get("trend_summary", {})
        if trend.get("increasing", 0) > trend.get("decreasing", 0):
            recommendations.append("Overall demand trend increasing - review inventory levels across categories")

        return recommendations

    def generate_forecast(
        self,
        sku: Optional[str] = None,
        store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate forecasts using ML models.

        Args:
            sku: Optional SKU to forecast
            store_id: Optional store ID

        Returns:
            Forecast results
        """
        try:
            from ml.inference.predict_demand_service import demand_prediction_service

            if sku and store_id:
                result = demand_prediction_service.predict_demand(sku, store_id, days_ahead=7)
            else:
                result = demand_prediction_service.generate_all_predictions(days_ahead=7)

            return result

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {"error": str(e)}

    def get_stockout_prediction(self, sku: str, location_id: str) -> Dict[str, Any]:
        """Predict when an item will stock out"""
        try:
            # Get current inventory
            inv = self.db.inventory.find_one({
                "sku": sku,
                "location_id": location_id
            })

            if not inv:
                return {"error": "Inventory not found"}

            current_stock = inv.get("current_stock", 0)
            reserved = inv.get("reserved_stock", 0)
            available = current_stock - reserved

            # Get forecast
            forecast = self.db.predicted_demand.find_one({
                "sku": sku,
                "store_id": location_id
            })

            if not forecast:
                # Use historical average
                daily_usage = inv.get("historical_avg_sales", 5)
            else:
                daily_usage = forecast.get("predicted_daily_avg", 5)

            if daily_usage <= 0:
                return {
                    "sku": sku,
                    "location_id": location_id,
                    "stockout_prediction": None,
                    "message": "Insufficient data to predict stockout"
                }

            days_until_stockout = available / daily_usage
            stockout_date = datetime.utcnow() + timedelta(days=days_until_stockout)

            return {
                "sku": sku,
                "location_id": location_id,
                "current_stock": current_stock,
                "available_stock": available,
                "daily_usage_rate": round(daily_usage, 1),
                "days_until_stockout": round(days_until_stockout, 1),
                "predicted_stockout_date": stockout_date.isoformat(),
                "risk_level": "critical" if days_until_stockout < 2 else "high" if days_until_stockout < 5 else "medium"
            }

        except Exception as e:
            logger.error(f"Error predicting stockout: {e}")
            return {"error": str(e)}


# Global instance
forecasting_agent = ForecastingAgent()
