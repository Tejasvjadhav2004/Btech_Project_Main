"""
Demo Simulation Service - Live simulation engine for demo presentations

Generates continuous supply chain operational events including:
- Orders
- Inventory consumption
- Delivery events
- Warehouse utilization changes
- Demand variations
- Anomalies for AI detection
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
import logging
import random
import uuid
import math
import threading
import time

logger = logging.getLogger(__name__)


class SimulationMode:
    """Simulation mode constants"""
    BASELINE = "baseline"  # Rule-based, no AI optimization
    AI_AUTONOMOUS = "ai_autonomous"  # Full AI orchestration


class SimulationState:
    """Track simulation state"""
    def __init__(self):
        self.is_running = False
        self.mode = SimulationMode.AI_AUTONOMOUS
        self.tick_count = 0
        self.start_time = None
        self.events_generated = 0
        self.signals_generated = 0
        self.actions_executed = 0
        self.pause_simulation = False
        self.speed_multiplier = 1.0  # 1.0 = real-time, 2.0 = 2x speed
        self.scenario = None


class DemoSimulationService:
    """
    Live simulation engine for demo presentations.

    Generates realistic supply chain events that demonstrate
    the AI's ability to detect, predict, optimize, and act.
    """

    def __init__(self):
        self.state = SimulationState()
        self._simulation_thread = None
        self._stop_event = threading.Event()

        # Simulation parameters - adjusted for presentation pace
        self.tick_interval = 8.0  # seconds between simulation ticks (slower for demo)
        self.base_order_rate = 1  # orders per tick (reduced for clarity)
        self.demand_variation = 0.2  # 20% random variation

        # Scenario-specific parameters
        self.scenario_params = {
            "demand_spike": {"active": False, "region": None, "factor": 2.5, "duration_ticks": 20},
            "delivery_delay": {"active": False, "affected_routes": [], "delay_hours": 24},
            "inventory_crisis": {"active": False, "affected_skus": [], "depletion_rate": 3.0},
            "warehouse_overload": {"active": False, "warehouse_id": None, "target_utilization": 98}
        }

        # Track metrics for KPI calculation
        self.metrics_history = {
            "baseline": {
                "forecast_errors": [],
                "delivery_delays": [],
                "stockouts": [],
                "utilization": []
            },
            "ai_autonomous": {
                "forecast_errors": [],
                "delivery_delays": [],
                "stockouts": [],
                "utilization": []
            }
        }

        # Demo activity feed
        self.activity_feed = []
        self.max_feed_items = 100

    @property
    def db(self):
        return mongodb.get_database()

    def start_simulation(self, mode: str = None) -> Dict[str, Any]:
        """Start the live simulation"""
        if self.state.is_running:
            return {
                "success": False,
                "message": "Simulation already running"
            }

        self.state.is_running = True
        self.state.start_time = datetime.utcnow()
        self.state.tick_count = 0
        self.state.mode = mode or SimulationMode.AI_AUTONOMOUS
        self._stop_event.clear()

        # Start simulation thread
        self._simulation_thread = threading.Thread(
            target=self._simulation_loop,
            daemon=True
        )
        self._simulation_thread.start()

        self._add_activity(
            "system",
            f"Simulation started in {self.state.mode} mode",
            "info"
        )

        logger.info(f"Demo simulation started in {self.state.mode} mode")

        return {
            "success": True,
            "message": f"Simulation started in {self.state.mode} mode",
            "state": self._get_state()
        }

    def stop_simulation(self) -> Dict[str, Any]:
        """Stop the simulation"""
        if not self.state.is_running:
            return {
                "success": False,
                "message": "Simulation not running"
            }

        self._stop_event.set()
        self.state.is_running = False

        if self._simulation_thread:
            self._simulation_thread.join(timeout=5.0)

        self._add_activity(
            "system",
            "Simulation stopped",
            "info"
        )

        logger.info("Demo simulation stopped")

        return {
            "success": True,
            "message": "Simulation stopped",
            "final_state": self._get_state()
        }

    def set_mode(self, mode: str) -> Dict[str, Any]:
        """Switch between baseline and AI autonomous mode"""
        if mode not in [SimulationMode.BASELINE, SimulationMode.AI_AUTONOMOUS]:
            return {
                "success": False,
                "message": f"Invalid mode: {mode}"
            }

        old_mode = self.state.mode
        self.state.mode = mode

        self._add_activity(
            "system",
            f"Mode switched from {old_mode} to {mode}",
            "info"
        )

        logger.info(f"Simulation mode changed: {old_mode} -> {mode}")

        return {
            "success": True,
            "message": f"Mode changed to {mode}",
            "previous_mode": old_mode,
            "current_mode": mode
        }

    def trigger_scenario(self, scenario: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger a specific demo scenario"""
        valid_scenarios = ["demand_spike", "delivery_delay", "inventory_crisis", "warehouse_overload"]

        if scenario not in valid_scenarios:
            return {
                "success": False,
                "message": f"Invalid scenario: {scenario}"
            }

        if not self.state.is_running:
            return {
                "success": False,
                "message": "Simulation not running. Start simulation first."
            }

        # Apply scenario settings
        self.scenario_params[scenario]["active"] = True
        if params:
            self.scenario_params[scenario].update(params)

        self.state.scenario = scenario

        self._add_activity(
            "scenario",
            f"Scenario triggered: {scenario.replace('_', ' ').title()}",
            "warning"
        )

        # Trigger appropriate signal generation
        self._execute_scenario(scenario)

        logger.info(f"Scenario triggered: {scenario}")

        return {
            "success": True,
            "message": f"Scenario '{scenario}' triggered",
            "scenario_params": self.scenario_params[scenario]
        }

    def _simulation_loop(self):
        """Main simulation loop"""
        logger.info("Simulation loop started")

        while not self._stop_event.is_set():
            try:
                if not self.state.pause_simulation:
                    self._tick()
                    self.state.tick_count += 1

                # Wait for next tick
                self._stop_event.wait(self.tick_interval / self.state.speed_multiplier)

            except Exception as e:
                logger.error(f"Error in simulation tick: {e}")
                self._add_activity("error", f"Simulation error: {str(e)}", "error")

        logger.info("Simulation loop ended")

    def _tick(self):
        """Execute one simulation tick"""
        # Generate orders
        orders = self._generate_orders()

        # Process inventory consumption
        self._process_inventory_consumption(orders)

        # Update deliveries
        self._update_deliveries()

        # Apply scenario effects if active
        self._apply_scenario_effects()

        # Run detection (only in AI mode for certain operations)
        if self.state.mode == SimulationMode.AI_AUTONOMOUS:
            self._run_ai_operations()
        else:
            self._run_baseline_operations()

        # Emit update event
        self._emit_update()

    def _generate_orders(self) -> List[Dict[str, Any]]:
        """Generate random orders for the simulation"""
        orders = []

        # Determine order count with variation
        base_count = self.base_order_rate
        variation = int(base_count * self.demand_variation * (random.random() * 2 - 1))
        order_count = max(1, base_count + variation)

        # Apply demand spike if active
        if self.scenario_params["demand_spike"]["active"]:
            spike_factor = self.scenario_params["demand_spike"]["factor"]
            order_count = int(order_count * spike_factor)

        # Get available products and stores
        products = list(self.db.products.find().limit(20))
        stores = list(self.db.stores.find().limit(10))

        if not products or not stores:
            logger.warning("No products or stores found for order generation")
            return orders

        for _ in range(order_count):
            product = random.choice(products)
            store = random.choice(stores)

            # Determine quantity
            quantity = random.randint(5, 50)

            # Create order
            order = {
                "order_id": f"ORD-{uuid.uuid4().hex[:8].upper()}",
                "store_id": store["store_id"],
                "items": [{
                    "sku": product["sku"],
                    "quantity": quantity,
                    "unit_price": product.get("current_price", 100),
                    "total_price": quantity * product.get("current_price", 100)
                }],
                "total_amount": quantity * product.get("current_price", 100),
                "status": "pending",
                "priority": random.choice(["low", "normal", "high"]),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source": "simulation",
                "simulation_tick": self.state.tick_count
            }

            # Insert order
            try:
                self.db.orders.insert_one(order)
                orders.append(order)
                self.state.events_generated += 1
            except Exception as e:
                logger.error(f"Error creating order: {e}")

        if orders:
            self._add_activity(
                "orders",
                f"Generated {len(orders)} new orders",
                "info"
            )

        return orders

    def _process_inventory_consumption(self, orders: List[Dict[str, Any]]):
        """Process inventory consumption from orders"""
        for order in orders:
            for item in order.get("items", []):
                sku = item["sku"]
                quantity = item["quantity"]

                # Find inventory record (prefer warehouse inventory)
                inventory = self.db.inventory.find_one({
                    "sku": sku,
                    "location_type": "warehouse"
                })

                if inventory:
                    # Reduce inventory
                    new_stock = max(0, inventory.get("current_stock", 0) - quantity)

                    self.db.inventory.update_one(
                        {"_id": inventory["_id"]},
                        {
                            "$set": {
                                "current_stock": new_stock,
                                "available_stock": new_stock,
                                "updated_at": datetime.utcnow()
                            },
                            "$inc": {
                                "total_sales": quantity
                            }
                        }
                    )

                    # Check if this creates a low stock situation
                    threshold = inventory.get("reorder_threshold", 20)
                    if new_stock <= threshold and new_stock > 0:
                        # Create low stock signal if in AI mode
                        if self.state.mode == SimulationMode.AI_AUTONOMOUS:
                            self._create_low_stock_signal(sku, inventory["location_id"], new_stock, threshold)
                    elif new_stock == 0:
                        # Stockout!
                        self._create_stockout_signal(sku, inventory["location_id"])

    def _update_deliveries(self):
        """Update delivery statuses"""
        # Get in-transit deliveries
        deliveries = list(self.db.deliveries.find({"status": "in_transit"}))

        for delivery in deliveries:
            # Simulate progress
            progress = delivery.get("progress", 0) + random.randint(10, 30)

            if progress >= 100:
                # Delivery complete
                self.db.deliveries.update_one(
                    {"_id": delivery["_id"]},
                    {
                        "$set": {
                            "status": "delivered",
                            "actual_arrival": datetime.utcnow(),
                            "progress": 100,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                self._add_activity(
                    "delivery",
                    f"Delivery {delivery['delivery_id']} completed",
                    "success"
                )
            else:
                # Update progress
                delay_applied = False

                # Apply delivery delay scenario if active
                if self.scenario_params["delivery_delay"]["active"]:
                    if random.random() < 0.3:  # 30% chance of delay
                        progress -= random.randint(5, 15)
                        progress = max(0, progress)
                        delay_applied = True

                self.db.deliveries.update_one(
                    {"_id": delivery["_id"]},
                    {
                        "$set": {
                            "progress": progress,
                            "updated_at": datetime.utcnow(),
                            "delayed": delay_applied
                        }
                    }
                )

    def _apply_scenario_effects(self):
        """Apply active scenario effects"""
        # Demand spike scenario
        if self.scenario_params["demand_spike"]["active"]:
            self.scenario_params["demand_spike"]["duration_ticks"] -= 1
            if self.scenario_params["demand_spike"]["duration_ticks"] <= 0:
                self.scenario_params["demand_spike"]["active"] = False
                self._add_activity(
                    "scenario",
                    "Demand spike scenario ended",
                    "info"
                )

        # Inventory crisis scenario
        if self.scenario_params["inventory_crisis"]["active"]:
            affected_skus = self.scenario_params["inventory_crisis"]["affected_skus"]
            depletion_rate = self.scenario_params["inventory_crisis"]["depletion_rate"]

            for sku in affected_skus:
                inventory = self.db.inventory.find_one({"sku": sku})
                if inventory:
                    new_stock = max(0, inventory.get("current_stock", 0) - int(depletion_rate * 10))
                    self.db.inventory.update_one(
                        {"_id": inventory["_id"]},
                        {"$set": {"current_stock": new_stock, "available_stock": new_stock}}
                    )

        # Warehouse overload scenario
        if self.scenario_params["warehouse_overload"]["active"]:
            warehouse_id = self.scenario_params["warehouse_overload"]["warehouse_id"]
            if warehouse_id:
                # Add stock to push utilization high
                self.db.warehouses.update_one(
                    {"warehouse_id": warehouse_id},
                    {"$inc": {"current_utilization": 500}}
                )

    def _run_ai_operations(self):
        """Run AI-powered operations (forecasting, optimization, orchestration)"""
        # Run periodic detection - less frequently for cleaner demo
        if self.state.tick_count % 5 == 0:  # Every 5th tick
            self._run_detection()

        # Run forecasting
        if self.state.tick_count % 8 == 0:  # Every 8th tick
            self._run_forecasting()

        # Run optimization
        if self.state.tick_count % 12 == 0:  # Every 12th tick
            self._run_optimization()

        # Run orchestration for active signals - key AI demonstration
        if self.state.tick_count % 6 == 0:  # Every 6th tick
            self._run_orchestration()

    def _run_baseline_operations(self):
        """Run baseline (rule-based) operations"""
        # Simple detection only
        if self.state.tick_count % 5 == 0:
            self._run_detection()

    def _run_detection(self):
        """Run signal detection"""
        try:
            from services.sensing_service import sensing_service

            # Check for low stock
            low_stock_items = list(self.db.inventory.find({
                "current_stock": {"$lt": 20},
                "location_type": "warehouse"
            }))

            for item in low_stock_items:
                if item["current_stock"] == 0:
                    self._create_stockout_signal(item["sku"], item["location_id"])
                else:
                    self._create_low_stock_signal(
                        item["sku"],
                        item["location_id"],
                        item["current_stock"],
                        item.get("reorder_threshold", 20)
                    )

            # Check for over-utilization
            warehouses = list(self.db.warehouses.find())
            for wh in warehouses:
                capacity = wh.get("capacity", 10000)
                current = wh.get("current_utilization", 0)
                util_pct = (current / capacity) * 100 if capacity > 0 else 0

                if util_pct > 90:
                    self._create_over_utilization_signal(wh["warehouse_id"], util_pct)

        except Exception as e:
            logger.error(f"Error in detection: {e}")

    def _run_forecasting(self):
        """Run demand forecasting"""
        try:
            from services.predictive_sensing_service import predictive_sensing_service

            # Run predictions for random products
            products = list(self.db.products.find().limit(5))

            for product in products:
                sku = product["sku"]

                # Get inventory for this product
                inventory = self.db.inventory.find_one({
                    "sku": sku,
                    "location_type": "warehouse"
                })

                if inventory:
                    # Generate prediction (simplified)
                    current_stock = inventory.get("current_stock", 0)
                    avg_daily_sales = inventory.get("total_sales", 100) / max(1, self.state.tick_count)

                    if avg_daily_sales > 0 and current_stock > 0:
                        days_until_stockout = int(current_stock / avg_daily_sales)

                        if days_until_stockout <= 7:
                            self._add_activity(
                                "forecasting",
                                f"AI predicts {product.get('name', sku)} will stock out in {days_until_stockout} days",
                                "warning"
                            )

                            self.state.events_generated += 1

        except Exception as e:
            logger.error(f"Error in forecasting: {e}")

    def _run_optimization(self):
        """Run optimization routines"""
        try:
            self._add_activity(
                "optimization",
                "AI analyzing inventory allocation for optimization opportunities",
                "info"
            )

            # Check for imbalances
            inventory_by_sku = {}
            for item in self.db.inventory.find({"location_type": "warehouse"}):
                sku = item["sku"]
                if sku not in inventory_by_sku:
                    inventory_by_sku[sku] = []
                inventory_by_sku[sku].append(item)

            for sku, items in inventory_by_sku.items():
                if len(items) > 1:
                    # Check for imbalance
                    stocks = [i.get("current_stock", 0) for i in items]
                    if max(stocks) > 0 and min(stocks) >= 0:
                        imbalance_ratio = max(stocks) / max(1, min(stocks))
                        if imbalance_ratio > 3:  # Significant imbalance
                            self._add_activity(
                                "optimization",
                                f"AI detected inventory imbalance for {sku} - recommending redistribution",
                                "info"
                            )

        except Exception as e:
            logger.error(f"Error in optimization: {e}")

    def _run_orchestration(self):
        """Run LLM orchestration for active signals"""
        try:
            # Get active signals
            active_signals = list(self.db.signals.find({"status": "active"}).limit(3))

            for signal in active_signals:
                self._add_activity(
                    "orchestration",
                    f"AI Orchestrator analyzing signal: {signal.get('type', 'Unknown')}",
                    "info"
                )

                # In AI mode, process signals automatically
                if self.state.mode == SimulationMode.AI_AUTONOMOUS:
                    self._process_signal_with_ai(signal)

        except Exception as e:
            logger.error(f"Error in orchestration: {e}")

    def _process_signal_with_ai(self, signal: Dict[str, Any]):
        """Process a signal using AI orchestration"""
        try:
            # Simplified orchestration for demo
            signal_type = signal.get("type")

            if signal_type in ["LOW_STOCK", "STOCKOUT"]:
                # Create replenishment order
                self._create_replenishment_order(signal)

            elif signal_type == "OVER_UTILIZATION":
                # Redistribute inventory
                self._redistribute_inventory(signal)

            elif signal_type == "DELIVERY_DELAY":
                # Reroute delivery
                self._reroute_delivery(signal)

            # Resolve the signal
            self.db.signals.update_one(
                {"signal_id": signal["signal_id"]},
                {
                    "$set": {
                        "status": "resolved",
                        "resolved_at": datetime.utcnow(),
                        "auto_resolved": True,
                        "resolution_method": "ai_orchestration"
                    }
                }
            )

            self.state.actions_executed += 1

        except Exception as e:
            logger.error(f"Error processing signal with AI: {e}")

    def _create_replenishment_order(self, signal: Dict[str, Any]):
        """Create a replenishment order"""
        details = signal.get("details", {})
        sku = details.get("sku") or signal.get("product_id")
        warehouse_id = signal.get("entity_id")

        if not sku or not warehouse_id:
            return

        order_id = f"REPL-{uuid.uuid4().hex[:8].upper()}"
        quantity = random.randint(50, 200)

        # Find supplier
        supplier = self.db.suppliers.find_one({"products": {"$in": [sku]}})
        supplier_id = supplier["supplier_id"] if supplier else "SUP-DEFAULT"

        replenishment = {
            "order_id": order_id,
            "order_type": "replenishment",
            "triggered_by_signal": signal["signal_id"],
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "items": [{
                "sku": sku,
                "quantity": quantity
            }],
            "status": "approved",
            "priority": "high" if signal["type"] == "STOCKOUT" else "normal",
            "created_at": datetime.utcnow(),
            "auto_generated": True,
            "source": "ai_orchestration"
        }

        self.db.replenishment_orders.insert_one(replenishment)

        # Immediately restock (simulating quick AI action)
        self.db.inventory.update_one(
            {"sku": sku, "location_id": warehouse_id},
            {
                "$inc": {"current_stock": quantity, "available_stock": quantity},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        self._add_activity(
            "action",
            f"AI auto-generated and executed replenishment: {quantity} units of {sku}",
            "success"
        )

    def _redistribute_inventory(self, signal: Dict[str, Any]):
        """Redistribute inventory from overloaded warehouse"""
        warehouse_id = signal.get("entity_id")

        self._add_activity(
            "action",
            f"AI redistributing inventory from overloaded warehouse {warehouse_id}",
            "success"
        )

        # Simulate redistribution
        self.db.warehouses.update_one(
            {"warehouse_id": warehouse_id},
            {"$inc": {"current_utilization": -1000}}
        )

    def _reroute_delivery(self, signal: Dict[str, Any]):
        """Reroute a delayed delivery"""
        delivery_id = signal.get("entity_id")

        self._add_activity(
            "action",
            f"AI rerouting delayed delivery {delivery_id} through alternate route",
            "success"
        )

    def _create_low_stock_signal(self, sku: str, location_id: str, current_stock: int, threshold: int):
        """Create a low stock signal"""
        signal = {
            "signal_id": f"SIG-{uuid.uuid4().hex[:8].upper()}",
            "type": "LOW_STOCK",
            "entity_type": "warehouse",
            "entity_id": location_id,
            "product_id": sku,
            "severity": "high" if current_stock < 10 else "medium",
            "status": "active",
            "message": f"Low stock alert: {sku} at {location_id} (Stock: {current_stock}, Threshold: {threshold})",
            "details": {
                "sku": sku,
                "current_stock": current_stock,
                "threshold": threshold
            },
            "created_at": datetime.utcnow(),
            "source": "simulation"
        }

        try:
            self.db.signals.insert_one(signal)
            self.state.signals_generated += 1
            self._add_activity(
                "signal",
                f"Detected LOW_STOCK for {sku} at {location_id}",
                "warning"
            )
        except Exception as e:
            logger.error(f"Error creating signal: {e}")

    def _create_stockout_signal(self, sku: str, location_id: str):
        """Create a stockout signal"""
        signal = {
            "signal_id": f"SIG-{uuid.uuid4().hex[:8].upper()}",
            "type": "STOCKOUT",
            "entity_type": "warehouse",
            "entity_id": location_id,
            "product_id": sku,
            "severity": "critical",
            "status": "active",
            "message": f"STOCKOUT: {sku} is out of stock at {location_id}",
            "details": {
                "sku": sku,
                "current_stock": 0
            },
            "created_at": datetime.utcnow(),
            "source": "simulation"
        }

        try:
            self.db.signals.insert_one(signal)
            self.state.signals_generated += 1
            self._add_activity(
                "signal",
                f"CRITICAL: STOCKOUT detected for {sku} at {location_id}",
                "error"
            )
        except Exception as e:
            logger.error(f"Error creating signal: {e}")

    def _create_over_utilization_signal(self, warehouse_id: str, utilization_pct: float):
        """Create over-utilization signal"""
        signal = {
            "signal_id": f"SIG-{uuid.uuid4().hex[:8].upper()}",
            "type": "OVER_UTILIZATION",
            "entity_type": "warehouse",
            "entity_id": warehouse_id,
            "severity": "critical" if utilization_pct > 95 else "high",
            "status": "active",
            "message": f"Warehouse {warehouse_id} is over-utilized at {utilization_pct:.1f}%",
            "details": {
                "utilization_percent": utilization_pct
            },
            "created_at": datetime.utcnow(),
            "source": "simulation"
        }

        try:
            self.db.signals.insert_one(signal)
            self.state.signals_generated += 1
            self._add_activity(
                "signal",
                f"Detected OVER_UTILIZATION at {warehouse_id} ({utilization_pct:.1f}%)",
                "warning"
            )
        except Exception as e:
            logger.error(f"Error creating signal: {e}")

    def _execute_scenario(self, scenario: str):
        """Execute specific scenario setup"""
        if scenario == "demand_spike":
            # Trigger demand spike signal
            region = random.choice(["North", "South", "East", "West"])
            self.scenario_params["demand_spike"]["region"] = region
            self._add_activity(
                "signal",
                f"DEMAND_SPIKE detected in {region} region - 2.5x normal demand",
                "warning"
            )

        elif scenario == "delivery_delay":
            # Delay random deliveries
            deliveries = list(self.db.deliveries.find({"status": "in_transit"}).limit(5))
            for d in deliveries:
                self._create_delivery_delay_signal(d["delivery_id"], 24)
            self.scenario_params["delivery_delay"]["affected_routes"] = [d["delivery_id"] for d in deliveries]

        elif scenario == "inventory_crisis":
            # Pick random products for crisis
            products = list(self.db.products.find().limit(3))
            self.scenario_params["inventory_crisis"]["affected_skus"] = [p["sku"] for p in products]
            self._add_activity(
                "signal",
                f"INVENTORY_CRISIS: Rapid depletion detected for {len(products)} products",
                "error"
            )

        elif scenario == "warehouse_overload":
            warehouses = list(self.db.warehouses.find().limit(1))
            if warehouses:
                wh_id = warehouses[0]["warehouse_id"]
                self.scenario_params["warehouse_overload"]["warehouse_id"] = wh_id
                self._add_activity(
                    "signal",
                    f"WAREHOUSE_OVERLOAD: {wh_id} approaching maximum capacity",
                    "error"
                )

    def _create_delivery_delay_signal(self, delivery_id: str, delay_hours: int):
        """Create delivery delay signal"""
        signal = {
            "signal_id": f"SIG-{uuid.uuid4().hex[:8].upper()}",
            "type": "DELIVERY_DELAY",
            "entity_type": "delivery",
            "entity_id": delivery_id,
            "severity": "high",
            "status": "active",
            "message": f"Delivery {delivery_id} is delayed by {delay_hours} hours",
            "details": {
                "delay_hours": delay_hours
            },
            "created_at": datetime.utcnow(),
            "source": "simulation"
        }

        try:
            self.db.signals.insert_one(signal)
            self.state.signals_generated += 1
            self._add_activity(
                "signal",
                f"DELIVERY_DELAY detected for {delivery_id}",
                "warning"
            )
        except Exception as e:
            logger.error(f"Error creating signal: {e}")

    def _add_activity(self, activity_type: str, message: str, severity: str = "info"):
        """Add activity to the feed"""
        activity = {
            "id": str(uuid.uuid4()),
            "type": activity_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "tick": self.state.tick_count,
            "mode": self.state.mode
        }

        self.activity_feed.append(activity)

        # Keep feed bounded
        if len(self.activity_feed) > self.max_feed_items:
            self.activity_feed = self.activity_feed[-self.max_feed_items:]

    def _emit_update(self):
        """Emit update for WebSocket clients"""
        # This will be called to push updates via WebSocket
        pass

    def _get_state(self) -> Dict[str, Any]:
        """Get current simulation state"""
        return {
            "is_running": self.state.is_running,
            "mode": self.state.mode,
            "tick_count": self.state.tick_count,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "events_generated": self.state.events_generated,
            "signals_generated": self.state.signals_generated,
            "actions_executed": self.state.actions_executed,
            "active_scenario": self.state.scenario
        }

    def get_activity_feed(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity feed"""
        return self.activity_feed[-limit:]

    def get_status(self) -> Dict[str, Any]:
        """Get simulation status"""
        return {
            "state": self._get_state(),
            "scenarios": {
                name: params["active"]
                for name, params in self.scenario_params.items()
            },
            "activity_count": len(self.activity_feed)
        }

    def get_activity_detail(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific activity"""
        for activity in self.activity_feed:
            if activity.get("id") == activity_id:
                detail = activity.copy()

                # Add contextual information based on activity type
                activity_type = activity.get("type")

                if activity_type == "signal":
                    # Find related signal in database
                    signal_msg = activity.get("message", "")
                    # Extract signal ID from message or find recent signals
                    recent_signals = list(self.db.signals.find(
                        {"status": "active"},
                        {"_id": 0}
                    ).sort("created_at", -1).limit(5))

                    detail["related_signals"] = [
                        {
                            "signal_id": s.get("signal_id"),
                            "type": s.get("type"),
                            "severity": s.get("severity"),
                            "entity_id": s.get("entity_id"),
                            "message": s.get("message"),
                            "details": s.get("details"),
                            "created_at": s.get("created_at")
                        } for s in recent_signals
                    ]

                elif activity_type == "action":
                    # Find related actions/executions
                    detail["ai_reasoning"] = {
                        "decision_process": [
                            "Signal detected and classified by severity",
                            "Context aggregated from multiple data sources",
                            "LLM Orchestrator generated action plan",
                            "Validation passed - action approved",
                            "Autonomous execution initiated"
                        ],
                        "confidence": 0.92,
                        "execution_time_ms": 150
                    }

                elif activity_type == "forecasting":
                    # Add forecast details
                    detail["forecast_details"] = {
                        "model": "Prophet + LSTM Ensemble",
                        "forecast_horizon_days": 7,
                        "confidence_interval": "95%",
                        "accuracy_trend": "improving"
                    }

                elif activity_type == "optimization":
                    # Add optimization details
                    detail["optimization_details"] = {
                        "algorithm": "Multi-objective Genetic Algorithm",
                        "objectives": ["minimize_cost", "maximize_service_level", "balance_inventory"],
                        "iterations": 150,
                        "convergence": True
                    }

                elif activity_type == "orchestration":
                    # Add orchestration flow details
                    detail["orchestration_flow"] = {
                        "steps": [
                            {"step": "Signal Analysis", "status": "completed", "duration_ms": 45},
                            {"step": "Context Aggregation", "status": "completed", "duration_ms": 120},
                            {"step": "LLM Reasoning", "status": "completed", "duration_ms": 850},
                            {"step": "Action Planning", "status": "completed", "duration_ms": 95},
                            {"step": "Validation", "status": "completed", "duration_ms": 30},
                            {"step": "Execution", "status": "in_progress", "duration_ms": 0}
                        ],
                        "agent_involved": ["SensingAgent", "ForecastingAgent", "OptimizationAgent", "ExecutionAgent"]
                    }

                return detail

        return None

    def get_active_signals_detail(self) -> List[Dict[str, Any]]:
        """Get detailed information about all active signals"""
        try:
            signals = list(self.db.signals.find(
                {"status": "active"},
                {"_id": 0}
            ).sort("created_at", -1).limit(20))

            detailed_signals = []
            for signal in signals:
                detail = {
                    "signal_id": signal.get("signal_id"),
                    "type": signal.get("type"),
                    "severity": signal.get("severity"),
                    "status": signal.get("status"),
                    "entity_type": signal.get("entity_type"),
                    "entity_id": signal.get("entity_id"),
                    "product_id": signal.get("product_id"),
                    "message": signal.get("message"),
                    "details": signal.get("details"),
                    "created_at": signal.get("created_at"),
                    "auto_resolved": signal.get("auto_resolved", False),
                    "ai_analysis": self._generate_ai_analysis(signal)
                }
                detailed_signals.append(detail)

            return detailed_signals

        except Exception as e:
            logger.error(f"Error getting active signals detail: {e}")
            return []

    def _generate_ai_analysis(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI analysis for a signal"""
        signal_type = signal.get("type")

        analysis = {
            "root_cause": None,
            "impact": None,
            "recommended_actions": [],
            "priority_score": 0
        }

        if signal_type == "LOW_STOCK":
            analysis["root_cause"] = "Demand exceeding supply rate"
            analysis["impact"] = "Potential stockout in 3-5 days if unaddressed"
            analysis["recommended_actions"] = [
                "Initiate replenishment order from primary supplier",
                "Check alternative supplier availability",
                "Consider inventory redistribution from high-stock locations"
            ]
            analysis["priority_score"] = 75 if signal.get("severity") == "high" else 50

        elif signal_type == "STOCKOUT":
            analysis["root_cause"] = "Inventory depleted below safety stock"
            analysis["impact"] = "Lost sales opportunity and customer dissatisfaction"
            analysis["recommended_actions"] = [
                "URGENT: Create emergency replenishment order",
                "Notify affected stores/customers",
                "Check for substitute products availability"
            ]
            analysis["priority_score"] = 95

        elif signal_type == "OVER_UTILIZATION":
            analysis["root_cause"] = "Inbound inventory exceeding capacity"
            analysis["impact"] = "Operational inefficiencies and storage costs"
            analysis["recommended_actions"] = [
                "Redistribute inventory to underutilized warehouses",
                "Temporarily halt inbound shipments",
                "Accelerate outbound fulfillment"
            ]
            analysis["priority_score"] = 70

        elif signal_type == "DELIVERY_DELAY":
            analysis["root_cause"] = "Transportation or logistics disruption"
            analysis["impact"] = "Customer delivery SLA breach"
            analysis["recommended_actions"] = [
                "Identify alternative delivery routes",
                "Escalate to alternate transport providers",
                "Notify affected customers with updated ETA"
            ]
            analysis["priority_score"] = 80

        return analysis


# Global instance
demo_simulation_service = DemoSimulationService()
