"""
Predictive Sensing Service - Detects future operational risks

Uses ML predictions to identify risks before they occur:
- Predicted stockout detection
- Future overload risk
- Demand surge forecasting
- Predicted delivery delays
"""
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
from services.signal_service import SignalService, SignalType, SignalSeverity, SignalStatus
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class PredictiveSignalType:
    """Predictive signal type constants"""
    PREDICTED_STOCKOUT = "PREDICTED_STOCKOUT"
    PREDICTED_DELAY = "PREDICTED_DELAY"
    DEMAND_SURGE_FORECAST = "DEMAND_SURGE_FORECAST"
    PREDICTED_OVER_UTILIZATION = "PREDICTED_OVER_UTILIZATION"
    PREDICTED_UNDER_UTILIZATION = "PREDICTED_UNDER_UTILIZATION"


class PredictiveSensingService:
    """
    Detects future operational risks using ML predictions.

    This service extends the reactive SensingService with predictive capabilities.
    It generates signals for risks that are predicted to occur in the future.
    """

    COLLECTION_NAME = "predictive_risks"

    def __init__(self):
        self.signal_service = SignalService()

    @property
    def db(self):
        """Get database connection dynamically"""
        return mongodb.get_database()

    def _generate_risk_id(self) -> str:
        """Generate unique risk ID"""
        return f"RISK-{uuid.uuid4().hex[:8].upper()}"

    def detect_predicted_stockout(
        self,
        prediction_days: int = 7,
        source: str = "predictive_scheduler"
    ) -> Dict[str, Any]:
        """
        Detect predicted stockouts based on demand forecasts and current inventory.

        Core formula:
        DaysRemaining = CurrentStock / PredictedDailyDemand
        If DaysRemaining < LeadTime, generate PREDICTED_STOCKOUT signal.

        Args:
            prediction_days: Number of days ahead to predict
            source: Source of detection

        Returns:
            Detection result with count of risks identified
        """
        logger.info("Running predicted stockout detection...")

        try:
            # Get demand predictions
            predictions = list(self.db.predicted_demand.find({
                "confidence": {"$gte": 0.5}
            }))

            if not predictions:
                logger.info("No demand predictions available")
                return {
                    "detection_type": "predicted_stockout",
                    "risks_identified": 0,
                    "message": "No predictions available"
                }

            risks_identified = 0
            risks_created = []

            for pred in predictions:
                sku = pred.get("sku")
                store_id = pred.get("store_id")
                predicted_daily_demand = pred.get("predicted_daily_avg", 0)
                confidence = pred.get("confidence", 0)

                if predicted_daily_demand <= 0:
                    continue

                # Get current inventory
                inventory = self.db.inventory.find_one({
                    "sku": sku,
                    "location_id": store_id
                })

                if not inventory:
                    continue

                current_stock = inventory.get("quantity", 0)
                reserved = inventory.get("reserved_stock", 0)
                available_stock = current_stock - reserved
                reorder_threshold = inventory.get("reorder_threshold", settings.reorder_threshold)

                # Get product info for lead time
                product = self.db.products.find_one({"sku": sku})
                lead_time_days = 7  # Default lead time

                # Calculate days remaining
                days_remaining = available_stock / predicted_daily_demand if predicted_daily_demand > 0 else float('inf')

                # Determine severity based on days remaining
                if days_remaining <= lead_time_days:
                    # Risk: Will stock out before reorder arrives
                    severity = self._determine_stockout_severity(days_remaining, lead_time_days)

                    # Create predictive signal
                    signal = self.signal_service.create_signal(
                        signal_type=PredictiveSignalType.PREDICTED_STOCKOUT,
                        entity_type="store",
                        entity_id=store_id,
                        product_id=sku,
                        severity=severity,
                        details={
                            "sku": sku,
                            "store_id": store_id,
                            "current_stock": current_stock,
                            "available_stock": available_stock,
                            "predicted_daily_demand": round(predicted_daily_demand, 2),
                            "days_remaining": round(days_remaining, 1),
                            "lead_time_days": lead_time_days,
                            "reorder_threshold": reorder_threshold,
                            "prediction_confidence": confidence,
                            "stockout_date": (datetime.utcnow() + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
                        },
                        threshold={
                            "lead_time_days": lead_time_days,
                            "prediction_window_days": prediction_days
                        },
                        source=source
                    )

                    if signal and signal.get("status") == "active":
                        risks_identified += 1
                        risks_created.append({
                            "sku": sku,
                            "store_id": store_id,
                            "days_remaining": round(days_remaining, 1),
                            "severity": severity
                        })

            result = {
                "detection_type": "predicted_stockout",
                "risks_identified": risks_identified,
                "predictions_analyzed": len(predictions),
                "threshold_days": prediction_days,
                "timestamp": datetime.utcnow().isoformat(),
                "risks": risks_created[:10]  # Top 10 for logging
            }

            logger.info(f"Predicted stockout detection complete: {risks_identified} risks identified")
            return result

        except Exception as e:
            logger.error(f"Error in predicted stockout detection: {e}")
            raise

    def _determine_stockout_severity(self, days_remaining: float, lead_time: int) -> str:
        """Determine severity based on days remaining until stockout"""
        if days_remaining <= 1:
            return SignalSeverity.CRITICAL
        elif days_remaining <= lead_time * 0.3:
            return SignalSeverity.HIGH
        elif days_remaining <= lead_time * 0.6:
            return SignalSeverity.MEDIUM
        else:
            return SignalSeverity.LOW

    def detect_demand_surge_forecast(
        self,
        surge_threshold: float = 1.5,
        source: str = "predictive_scheduler"
    ) -> Dict[str, Any]:
        """
        Detect forecasted demand surges (significant increase in predicted demand).

        Args:
            surge_threshold: Multiplier for considering a surge (1.5 = 50% increase)
            source: Source of detection

        Returns:
            Detection result
        """
        logger.info("Running demand surge forecast detection...")

        try:
            # Get predictions with increasing trend
            predictions = list(self.db.predicted_demand.find({
                "trend": "increasing"
            }))

            risks_identified = 0
            surges_detected = []

            for pred in predictions:
                sku = pred.get("sku")
                store_id = pred.get("store_id")
                predicted_demand_7d = pred.get("predicted_demand_7d", 0)
                confidence = pred.get("confidence", 0)

                # Get historical average demand
                historical_stats = self._get_historical_demand(sku, store_id)
                historical_avg_7d = historical_stats.get("avg_7d", 0)

                if historical_avg_7d > 0:
                    surge_factor = predicted_demand_7d / historical_avg_7d

                    if surge_factor >= surge_threshold:
                        # Determine severity
                        if surge_factor >= 2.0:
                            severity = SignalSeverity.CRITICAL
                        elif surge_factor >= 1.75:
                            severity = SignalSeverity.HIGH
                        else:
                            severity = SignalSeverity.MEDIUM

                        signal = self.signal_service.create_signal(
                            signal_type=PredictiveSignalType.DEMAND_SURGE_FORECAST,
                            entity_type="store",
                            entity_id=store_id,
                            product_id=sku,
                            severity=severity,
                            details={
                                "sku": sku,
                                "store_id": store_id,
                                "predicted_demand_7d": round(predicted_demand_7d, 2),
                                "historical_avg_7d": round(historical_avg_7d, 2),
                                "surge_factor": round(surge_factor, 2),
                                "confidence": confidence
                            },
                            threshold={"surge_threshold": surge_threshold},
                            source=source
                        )

                        if signal and signal.get("status") == "active":
                            risks_identified += 1
                            surges_detected.append({
                                "sku": sku,
                                "store_id": store_id,
                                "surge_factor": round(surge_factor, 2)
                            })

            result = {
                "detection_type": "demand_surge_forecast",
                "risks_identified": risks_identified,
                "predictions_analyzed": len(predictions),
                "surge_threshold": surge_threshold,
                "timestamp": datetime.utcnow().isoformat(),
                "surges": surges_detected[:10]
            }

            logger.info(f"Demand surge forecast complete: {risks_identified} surges detected")
            return result

        except Exception as e:
            logger.error(f"Error in demand surge forecast: {e}")
            raise

    def _get_historical_demand(self, sku: str, store_id: str) -> Dict[str, float]:
        """Get historical demand statistics"""
        try:
            pipeline = [
                {"$match": {"sku": sku, "location_id": store_id}},
                {"$group": {
                    "_id": None,
                    "avg_daily": {"$avg": "$quantity"},
                    "total": {"$sum": "$quantity"}
                }}
            ]

            collection = self.db["transactions"]
            result = list(collection.aggregate(pipeline))

            if result:
                avg_daily = result[0].get("avg_daily", 5)
                return {
                    "avg_daily": avg_daily,
                    "avg_7d": avg_daily * 7
                }

            return {"avg_daily": 5, "avg_7d": 35}

        except Exception:
            return {"avg_daily": 5, "avg_7d": 35}

    def detect_predicted_over_utilization(
        self,
        threshold: float = 90.0,
        source: str = "predictive_scheduler"
    ) -> Dict[str, Any]:
        """
        Detect predicted warehouse over-utilization based on demand forecasts.

        Args:
            threshold: Utilization percentage threshold
            source: Source of detection

        Returns:
            Detection result
        """
        logger.info("Running predicted over-utilization detection...")

        try:
            # Get warehouse data
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            predictions = list(self.db.predicted_demand.find())

            risks_identified = 0
            risks_created = []

            for warehouse in warehouses:
                warehouse_id = warehouse.get("warehouse_id")
                capacity = warehouse.get("capacity", 1000)
                current_utilization = warehouse.get("current_utilization", 0)

                # Get predictions for this warehouse's stores
                # (This would need store-warehouse mapping)
                predicted_increase = self._calculate_predicted_warehouse_demand(
                    warehouse_id, predictions
                )

                predicted_utilization = current_utilization + predicted_increase
                predicted_utilization_pct = (predicted_utilization / capacity) * 100

                if predicted_utilization_pct >= threshold:
                    severity = SignalSeverity.CRITICAL if predicted_utilization_pct >= 95 else SignalSeverity.HIGH

                    signal = self.signal_service.create_signal(
                        signal_type=PredictiveSignalType.PREDICTED_OVER_UTILIZATION,
                        entity_type="warehouse",
                        entity_id=warehouse_id,
                        severity=severity,
                        details={
                            "warehouse_id": warehouse_id,
                            "warehouse_name": warehouse.get("name"),
                            "capacity": capacity,
                            "current_utilization": current_utilization,
                            "current_utilization_pct": round((current_utilization / capacity) * 100, 2),
                            "predicted_increase": round(predicted_increase, 2),
                            "predicted_utilization_pct": round(predicted_utilization_pct, 2),
                            "threshold": threshold
                        },
                        threshold={"utilization_threshold": threshold},
                        source=source
                    )

                    if signal and signal.get("status") == "active":
                        risks_identified += 1
                        risks_created.append({
                            "warehouse_id": warehouse_id,
                            "predicted_utilization_pct": round(predicted_utilization_pct, 2)
                        })

            result = {
                "detection_type": "predicted_over_utilization",
                "risks_identified": risks_identified,
                "warehouses_checked": len(warehouses),
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat(),
                "risks": risks_created
            }

            logger.info(f"Predicted over-utilization detection complete: {risks_identified} risks")
            return result

        except Exception as e:
            logger.error(f"Error in predicted over-utilization detection: {e}")
            raise

    def _calculate_predicted_warehouse_demand(
        self,
        warehouse_id: str,
        predictions: List[Dict]
    ) -> float:
        """Calculate predicted demand increase for a warehouse"""
        total_predicted = 0

        for pred in predictions:
            # Check if this prediction is for a store served by this warehouse
            # This is simplified - in production, use proper store-warehouse mapping
            if warehouse_id in pred.get("store_id", ""):
                total_predicted += pred.get("predicted_demand_7d", 0)

        return total_predicted

    def run_all_predictive_detections(self, source: str = "predictive_scheduler") -> Dict[str, Any]:
        """
        Run all predictive detection functions.

        Returns:
            Combined results from all predictions
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "detections": {}
        }

        results["detections"]["predicted_stockout"] = self.detect_predicted_stockout(source=source)
        results["detections"]["demand_surge_forecast"] = self.detect_demand_surge_forecast(source=source)
        results["detections"]["predicted_over_utilization"] = self.detect_predicted_over_utilization(source=source)

        # Summary
        total_risks = sum(
            d.get("risks_identified", 0)
            for d in results["detections"].values()
        )
        results["total_risks_identified"] = total_risks

        logger.info(f"All predictive detections complete: {total_risks} total risks identified")
        return results

    def get_predictive_risks(
        self,
        risk_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get predictive risks from the signals collection.

        Args:
            risk_type: Optional filter by risk type
            severity: Optional filter by severity
            limit: Maximum number of results

        Returns:
            List of predictive risk signals
        """
        query = {
            "type": {"$in": [
                PredictiveSignalType.PREDICTED_STOCKOUT,
                PredictiveSignalType.PREDICTED_DELAY,
                PredictiveSignalType.DEMAND_SURGE_FORECAST,
                PredictiveSignalType.PREDICTED_OVER_UTILIZATION
            ]},
            "status": SignalStatus.ACTIVE
        }

        if risk_type:
            query["type"] = risk_type
        if severity:
            query["severity"] = severity

        risks = list(self.db.signals.find(query).sort([
            ("severity", -1),
            ("created_at", -1)
        ]).limit(limit))

        for risk in risks:
            risk["id"] = str(risk.pop("_id"))

        return risks


predictive_sensing_service = PredictiveSensingService()
