"""
Sensing Agent - Handles anomaly detection and signal processing

Part of the multi-agent orchestration system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from services.sensing_service import sensing_service
from services.signal_service import SignalService, SignalType, SignalStatus
from db.connection import mongodb
import logging

logger = logging.getLogger(__name__)


class SensingAgent:
    """
    Agent responsible for signal detection, prioritization, and alert management.

    Capabilities:
    - Detect anomalies across inventory, delivery, demand, and warehouse domains
    - Prioritize signals based on severity and business impact
    - Provide signal summaries for orchestration
    """

    AGENT_NAME = "sensing_agent"
    AGENT_TYPE = "sensing"

    def __init__(self):
        self.signal_service = SignalService()

    @property
    def db(self):
        return mongodb.get_database()

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context and generate signal-based insights.

        Args:
            context: Aggregated operational context

        Returns:
            Sensing agent output with prioritized signals
        """
        try:
            logger.info("Sensing Agent processing context")

            # Analyze current signals
            signals_analysis = self._analyze_signals(context.get("signals", {}))

            # Identify critical alerts
            critical_alerts = self._identify_critical_alerts(context)

            # Prioritize signals
            prioritized = self._prioritize_signals(signals_analysis)

            # Generate recommendations
            recommendations = self._generate_recommendations(signals_analysis, critical_alerts)

            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "timestamp": datetime.utcnow().isoformat(),
                "signals_analysis": signals_analysis,
                "critical_alerts": critical_alerts,
                "prioritized_signals": prioritized,
                "recommendations": recommendations,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Sensing Agent error: {e}")
            return {
                "agent": self.AGENT_NAME,
                "agent_type": self.AGENT_TYPE,
                "status": "error",
                "error": str(e)
            }

    def _analyze_signals(self, signals_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze signals from context"""
        analysis = {
            "total_active": signals_summary.get("total_active", 0),
            "by_type": signals_summary.get("by_type", {}),
            "by_severity": signals_summary.get("by_severity", {}),
            "critical_count": signals_summary.get("critical_count", 0),
            "high_count": signals_summary.get("high_count", 0),
            "immediate_attention": [],
            "patterns": []
        }

        # Identify signals needing immediate attention
        top_signals = signals_summary.get("top_signals", [])
        for signal in top_signals:
            if signal.get("severity") in ["critical", "high"]:
                analysis["immediate_attention"].append({
                    "signal_id": signal.get("signal_id"),
                    "type": signal.get("type"),
                    "severity": signal.get("severity"),
                    "entity_id": signal.get("entity_id")
                })

        # Detect patterns
        by_type = signals_summary.get("by_type", {})
        if by_type.get("LOW_STOCK", 0) > 3:
            analysis["patterns"].append("Multiple low stock alerts - systemic inventory issue")
        if by_type.get("STOCKOUT", 0) > 0:
            analysis["patterns"].append("Active stockouts detected - urgent replenishment needed")
        if by_type.get("DELIVERY_DELAY", 0) > 2:
            analysis["patterns"].append("Multiple delivery delays - logistics issue")

        return analysis

    def _identify_critical_alerts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical alerts from context"""
        alerts = []

        critical_issues = context.get("critical_issues", [])
        for issue in critical_issues:
            alerts.append({
                "alert_type": issue.get("type"),
                "severity": issue.get("severity"),
                "description": issue.get("description"),
                "entity_id": issue.get("entity_id"),
                "recommended_action": self._get_recommended_action(issue.get("type"))
            })

        return alerts

    def _get_recommended_action(self, issue_type: str) -> str:
        """Get recommended action for an issue type"""
        actions = {
            "stockout": "replenish_inventory",
            "warehouse_over_capacity": "rebalance_inventory",
            "severe_delivery_delay": "reroute_delivery",
            "low_stock": "replenish_inventory"
        }
        return actions.get(issue_type, "investigate")

    def _prioritize_signals(self, signals_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize signals for action"""
        prioritized = []

        # Start with immediate attention signals
        for signal in signals_analysis.get("immediate_attention", []):
            prioritized.append({
                "signal_id": signal.get("signal_id"),
                "priority": "immediate",
                "type": signal.get("type"),
                "severity": signal.get("severity"),
                "action_needed": True
            })

        # Add pattern-based priorities
        for pattern in signals_analysis.get("patterns", []):
            if "stockout" in pattern.lower():
                prioritized.append({
                    "priority": "immediate",
                    "pattern": pattern,
                    "action_needed": True
                })
            elif "multiple" in pattern.lower():
                prioritized.append({
                    "priority": "high",
                    "pattern": pattern,
                    "action_needed": True
                })

        return prioritized

    def _generate_recommendations(
        self,
        signals_analysis: Dict[str, Any],
        critical_alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if signals_analysis.get("critical_count", 0) > 0:
            recommendations.append("Address critical signals immediately before escalation")

        stockout_count = signals_analysis.get("by_type", {}).get("STOCKOUT", 0)
        if stockout_count > 0:
            recommendations.append(f"Initiate emergency replenishment for {stockout_count} stockout(s)")

        if signals_analysis.get("by_type", {}).get("DELIVERY_DELAY", 0) > 2:
            recommendations.append("Review logistics and consider alternative routes")

        for alert in critical_alerts[:3]:
            recommendations.append(f"Handle {alert.get('alert_type')}: {alert.get('description')}")

        return recommendations

    def run_detection(self, detection_type: str = "all") -> Dict[str, Any]:
        """
        Run specific detection manually.

        Args:
            detection_type: Type of detection to run

        Returns:
            Detection results
        """
        try:
            if detection_type == "all":
                result = sensing_service.run_all_detections(source="sensing_agent")
            elif detection_type == "low_stock":
                result = sensing_service.detect_low_stock(source="sensing_agent")
            elif detection_type == "stockout":
                result = sensing_service.detect_stockout(source="sensing_agent")
            elif detection_type == "delivery_delay":
                result = sensing_service.detect_delivery_delay(source="sensing_agent")
            elif detection_type == "demand_spike":
                result = sensing_service.detect_demand_spike(source="sensing_agent")
            elif detection_type == "utilization":
                result = sensing_service.detect_over_utilization(source="sensing_agent")
            else:
                return {"error": f"Unknown detection type: {detection_type}"}

            return result

        except Exception as e:
            logger.error(f"Error running detection: {e}")
            return {"error": str(e)}


# Global instance
sensing_agent = SensingAgent()
