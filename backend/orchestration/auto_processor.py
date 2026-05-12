"""
Auto Processor - Automatic Signal Processing for Orchestration

Monitors active signals and automatically triggers orchestration workflows.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from db.connection import mongodb
from orchestration.engine.orchestrator_service import orchestrator_service
from services.signal_service import signal_service, SignalStatus, SignalSeverity

logger = logging.getLogger(__name__)


class AutoProcessor:
    """
    Automatically processes signals through orchestration.

    Features:
    - Monitors active signals every 30 seconds
    - Auto-triggers orchestration for critical/high severity signals
    - Resolves signals when orchestration completes
    - Tracks processed signals to avoid duplication
    """

    def __init__(self):
        self._active = False
        self._task: Optional[asyncio.Task] = None
        self._processed_signals = set()  # Track recently processed signals
        self._last_cleanup = datetime.utcnow()

        # Configuration - process all severities for comprehensive automation
        self.auto_process_severities = {
            SignalSeverity.CRITICAL,
            SignalSeverity.HIGH,
            SignalSeverity.MEDIUM  # Added MEDIUM to handle predicted stockouts
        }
        self.auto_resolve_after_execution = True
        self.processing_interval_seconds = 30
        self.max_concurrent_workflows = 10

    def start(self):
        """Start the auto processor"""
        if self._active:
            logger.warning("Auto processor already running")
            return

        self._active = True
        self._task = asyncio.create_task(self._processing_loop())
        logger.info("Auto Processor started - monitoring signals for orchestration")

    def stop(self):
        """Stop the auto processor"""
        self._active = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Auto Processor stopped")

    def is_active(self) -> bool:
        """Check if auto processor is active"""
        return self._active

    async def _processing_loop(self):
        """Main processing loop"""
        logger.info("Auto Processor loop started")

        while self._active:
            try:
                await self._process_signals()
                await asyncio.sleep(self.processing_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Auto processor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _process_signals(self):
        """Process active signals through orchestration"""
        try:
            # Get active signals
            active_signals = signal_service.get_active_signals(limit=50)

            if not active_signals:
                return

            logger.info(f"Found {len(active_signals)} active signals")

            # Clean up old processed signals periodically
            if (datetime.utcnow() - self._last_cleanup).total_seconds() > 3600:
                self._cleanup_processed_signals()
                self._last_cleanup = datetime.utcnow()

            # Process each signal
            for signal in active_signals:
                await self._process_single_signal(signal)

        except Exception as e:
            logger.error(f"Error processing signals: {e}")

    async def _process_single_signal(self, signal: Dict[str, Any]):
        """
        Process a single signal through orchestration.

        Args:
            signal: Signal document to process
        """
        signal_id = signal.get("signal_id")
        signal_type = signal.get("type")
        severity = signal.get("severity")

        # Skip if already processed recently
        if signal_id in self._processed_signals:
            logger.debug(f"Signal {signal_id} already processed, skipping")
            return

        # Check if auto-processing is enabled for this severity
        if severity not in self.auto_process_severities:
            logger.debug(
                f"Signal {signal_id} has severity {severity}, "
                f"auto-processing disabled for this level"
            )
            return

        # Check orchestrator is active
        if not orchestrator_service.is_active():
            logger.warning("Orchestrator not active, cannot process signal")
            return

        logger.info(
            f"Auto-processing signal {signal_id}: {signal_type} ({severity})"
        )

        try:
            # First check if signal condition is still valid
            if self._check_signal_condition_resolved(signal):
                logger.info(f"Signal {signal_id} condition no longer exists, auto-resolving")
                signal_service.resolve_signal(
                    signal_id,
                    auto_resolved=True,
                    action_taken={"type": "condition_cleared"},
                    resolution_note="Signal condition no longer exists - auto-resolved"
                )
                self._processed_signals.add(signal_id)
                return

            # Prepare signal for orchestration
            orchestration_signal = self._prepare_orchestration_signal(signal)

            # Process through orchestration
            result = await orchestrator_service.process_signal(orchestration_signal)

            if result.get("success"):
                workflow_id = result.get("workflow_id")
                status = result.get("status")

                logger.info(
                    f"✓ Signal {signal_id} processed - "
                    f"Workflow {workflow_id} created with status: {status}"
                )

                # Mark as processed
                self._processed_signals.add(signal_id)

                # Check if workflow completed immediately (no approval needed)
                if status == "completed" and self.auto_resolve_after_execution:
                    # Resolve the signal
                    signal_service.resolve_signal(
                        signal_id,
                        auto_resolved=True,
                        action_taken={
                            "type": "orchestration",
                            "workflow_id": workflow_id,
                            "steps_executed": result.get("steps_executed", 0),
                            "execution_time": result.get("execution_time_seconds", 0)
                        },
                        resolution_note=f"Auto-resolved by orchestration workflow {workflow_id}"
                    )
                    logger.info(f"✓ Signal {signal_id} auto-resolved")

                elif status == "waiting_approval":
                    logger.info(f"Signal {signal_id} workflow awaiting approval: {workflow_id}")
                    # Acknowledge the signal but don't resolve yet
                    signal_service.acknowledge_signal(signal_id)

            else:
                error = result.get("error") or result.get("reason")
                logger.error(
                    f"✗ Failed to process signal {signal_id}: {error}"
                )

        except Exception as e:
            logger.error(f"Error processing signal {signal_id}: {e}")

    def _check_signal_condition_resolved(self, signal: Dict[str, Any]) -> bool:
        """
        Check if the signal's underlying condition has been resolved.

        This allows signals to be auto-resolved when the condition that
        triggered them no longer exists (e.g., inventory was replenished).
        """
        signal_type = signal.get("type")
        details = signal.get("details", {})
        entity_id = signal.get("entity_id")
        product_id = signal.get("product_id")

        from db.connection import mongodb
        db = mongodb.get_database()

        if signal_type in ["LOW_STOCK", "STOCKOUT", "PREDICTED_STOCKOUT"]:
            # Check if inventory is now above threshold
            if not (product_id and entity_id):
                return False

            inventory = db.inventory.find_one({
                "sku": product_id,
                "location_id": entity_id
            })

            if inventory:
                current_stock = inventory.get("current_stock", inventory.get("quantity", 0))
                reorder_threshold = inventory.get("reorder_threshold", 20)
                signal_threshold = details.get("threshold", reorder_threshold)

                # Signal is resolved if stock is now above reorder threshold
                # This is more accurate than using the signal's original threshold
                if signal_type == "STOCKOUT" and current_stock > 0:
                    return True
                if signal_type in ["LOW_STOCK", "PREDICTED_STOCKOUT"] and current_stock > reorder_threshold:
                    return True

        elif signal_type == "OVER_UTILIZATION":
            # Check if warehouse utilization is back to normal
            if not entity_id:
                return False

            warehouse = db.warehouses.find_one({"warehouse_id": entity_id})
            if warehouse:
                capacity = warehouse.get("capacity", 1)
                current_util = warehouse.get("current_utilization", 0)
                utilization_pct = (current_util / capacity * 100) if capacity > 0 else 0

                if utilization_pct < 90:  # Below critical threshold
                    return True

        elif signal_type == "DELIVERY_DELAY":
            # Check if delivery has been completed or rerouted
            delivery_id = details.get("delivery_id")
            if delivery_id:
                delivery = db.deliveries.find_one({"delivery_id": delivery_id})
                if delivery and delivery.get("status") in ["delivered", "completed"]:
                    return True

        return False

    def _prepare_orchestration_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare signal for orchestration processing.

        Maps signal fields to orchestration-expected format.
        """
        return {
            "signal_id": signal.get("signal_id"),
            "type": self._map_signal_type(signal.get("type")),
            "severity": signal.get("severity"),
            "entity_type": signal.get("entity_type"),
            "entity_id": signal.get("entity_id"),
            "product_id": signal.get("product_id"),
            "details": signal.get("details", {}),
            "threshold": signal.get("threshold", {}),
            "original_message": signal.get("message"),
            "created_at": signal.get("created_at")
        }

    def _map_signal_type(self, signal_type: str) -> str:
        """
        Map signal types to orchestration workflow types.

        Converts sensing layer signal types to orchestration workflow types.
        """
        type_mapping = {
            "STOCKOUT": "STOCKOUT_MITIGATION",
            "LOW_STOCK": "STOCKOUT_MITIGATION",
            "PREDICTED_STOCKOUT": "STOCKOUT_MITIGATION",
            "OVERSTOCK": "INVENTORY_REBALANCE",
            "OVER_UTILIZATION": "OVERLOAD_BALANCING",
            "PREDICTED_OVER_UTILIZATION": "OVERLOAD_BALANCING",
            "DELIVERY_DELAY": "DELAY_RECOVERY",
            "PREDICTED_DELAY": "DELAY_RECOVERY",
            "DEMAND_SPIKE": "DEMAND_SURGE_RESPONSE",
            "DEMAND_SURGE_FORECAST": "DEMAND_SURGE_RESPONSE",
            "DEMAND_DROP": "INVENTORY_REBALANCE",
            "UNDER_UTILIZATION": "INVENTORY_REBALANCE"
        }

        return type_mapping.get(signal_type, "STOCKOUT_MITIGATION")

    def _cleanup_processed_signals(self):
        """Clean up old processed signal IDs"""
        # Keep only last 1000 processed signals in memory
        if len(self._processed_signals) > 1000:
            self._processed_signals = set(list(self._processed_signals)[-500:])
            logger.info("Cleaned up processed signals cache")

    def get_status(self) -> Dict[str, Any]:
        """Get auto processor status"""
        return {
            "active": self._active,
            "processed_signals_count": len(self._processed_signals),
            "auto_process_severities": list(self.auto_process_severities),
            "processing_interval_seconds": self.processing_interval_seconds,
            "orchestrator_active": orchestrator_service.is_active()
        }


# Global auto processor instance
auto_processor = AutoProcessor()
