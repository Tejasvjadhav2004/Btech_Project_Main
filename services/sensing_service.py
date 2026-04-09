"""
Sensing Service - Detection engine for Sensing & Intelligence Layer

Implements all detection functions for identifying anomalies and patterns
in the supply chain system.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from db.connection import mongodb
from services.signal_service import SignalService, SignalType, SignalSeverity
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class SensingService:
    """
    Detection engine for supply chain anomalies and patterns.
    
    Detection Functions:
    - Inventory: detect_low_stock, detect_stockout, detect_overstock
    - Demand: detect_demand_spike, detect_demand_drop
    - Delivery: detect_delivery_delay
    - Warehouse: detect_over_utilization, detect_under_utilization
    """
    
    def __init__(self):
        self.db = mongodb.get_database()
        self.signal_service = SignalService()
    
    # ========================================
    # INVENTORY DETECTION FUNCTIONS
    # ========================================
    
    def detect_low_stock(
        self,
        threshold: int = None,
        location_type: str = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect inventory items below the low stock threshold.
        
        Creates LOW_STOCK signals for items that need attention.
        Does NOT create signals for stockout (quantity = 0).
        
        Args:
            threshold: Custom threshold (defaults to settings.low_stock_threshold)
            location_type: Filter by location type (warehouse, store)
            source: Source of detection (scheduler, event_trigger)
        
        Returns:
            Detection result with count of signals generated
        """
        if threshold is None:
            threshold = settings.low_stock_threshold
        
        try:
            # Build query for low stock (but not stockout)
            query = {
                "$expr": {
                    "$and": [
                        {"$gt": ["$quantity", 0]},  # Not stockout
                        {
                            "$lt": [
                                {"$subtract": ["$quantity", {"$ifNull": ["$reserved_stock", 0]}]},
                                threshold
                            ]
                        }
                    ]
                }
            }
            
            if location_type:
                query["location_type"] = location_type
            
            # Find all low stock items
            low_stock_items = list(self.db.inventory.find(query))
            
            signals_generated = 0
            items_checked = len(low_stock_items)
            
            for item in low_stock_items:
                sku = item.get("sku")
                location_id = item.get("location_id")
                loc_type = item.get("location_type", "warehouse")
                quantity = item.get("quantity", 0)
                reserved = item.get("reserved_stock", 0)
                available = quantity - reserved
                
                # Get product name
                product = self.db.products.find_one({"sku": sku})
                product_name = product.get("name", sku) if product else sku
                
                # Create signal
                signal = self.signal_service.create_signal(
                    signal_type=SignalType.LOW_STOCK,
                    entity_type=loc_type,
                    entity_id=location_id,
                    product_id=sku,
                    details={
                        "sku": sku,
                        "product_name": product_name,
                        "current_stock": quantity,
                        "reserved_stock": reserved,
                        "available_stock": available,
                        "threshold": threshold
                    },
                    threshold={"low_stock_threshold": threshold},
                    source=source
                )
                
                if signal and signal.get("status") == "active":
                    signals_generated += 1
            
            result = {
                "detection_type": "low_stock",
                "signals_generated": signals_generated,
                "items_checked": items_checked,
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Low stock detection complete: {signals_generated} signals "
                f"from {items_checked} items"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_low_stock: {e}")
            raise
    
    def detect_stockout(
        self,
        location_type: str = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect inventory items with zero available stock (stockout).
        
        Creates STOCKOUT signals (critical severity) for items that
        have no available inventory.
        
        Args:
            location_type: Filter by location type (warehouse, store)
            source: Source of detection
        
        Returns:
            Detection result with count of signals generated
        """
        try:
            # Build query for stockout (quantity = 0 OR available = 0)
            query = {
                "$or": [
                    {"quantity": 0},
                    {"quantity": {"$lte": {"$ifNull": ["$reserved_stock", 0]}}}
                ]
            }
            
            if location_type:
                query["location_type"] = location_type
            
            # Alternative simpler query
            stockout_items = list(self.db.inventory.find({
                "$expr": {
                    "$lte": [
                        {"$subtract": ["$quantity", {"$ifNull": ["$reserved_stock", 0]}]},
                        0
                    ]
                }
            }))
            
            if location_type:
                stockout_items = [i for i in stockout_items if i.get("location_type") == location_type]
            
            signals_generated = 0
            items_checked = len(stockout_items)
            
            for item in stockout_items:
                sku = item.get("sku")
                location_id = item.get("location_id")
                loc_type = item.get("location_type", "warehouse")
                quantity = item.get("quantity", 0)
                reserved = item.get("reserved_stock", 0)
                
                # Get product name
                product = self.db.products.find_one({"sku": sku})
                product_name = product.get("name", sku) if product else sku
                
                # Create CRITICAL signal for stockout
                signal = self.signal_service.create_signal(
                    signal_type=SignalType.STOCKOUT,
                    entity_type=loc_type,
                    entity_id=location_id,
                    product_id=sku,
                    severity=SignalSeverity.CRITICAL,
                    details={
                        "sku": sku,
                        "product_name": product_name,
                        "current_stock": quantity,
                        "reserved_stock": reserved,
                        "available_stock": 0
                    },
                    source=source
                )
                
                if signal and signal.get("status") == "active":
                    signals_generated += 1
            
            result = {
                "detection_type": "stockout",
                "signals_generated": signals_generated,
                "items_checked": items_checked,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Stockout detection complete: {signals_generated} signals "
                f"from {items_checked} items"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_stockout: {e}")
            raise
    
    def detect_overstock(
        self,
        multiplier: float = None,
        location_type: str = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect inventory items with excessive stock (overstock).
        
        Overstock is defined as having more than [multiplier]x the
        normal/expected stock level.
        
        Args:
            multiplier: Overstock multiplier (defaults to settings.overstock_multiplier)
            location_type: Filter by location type
            source: Source of detection
        
        Returns:
            Detection result with count of signals generated
        """
        if multiplier is None:
            multiplier = settings.overstock_multiplier
        
        try:
            # Get average stock levels per SKU
            pipeline = [
                {
                    "$group": {
                        "_id": "$sku",
                        "avg_quantity": {"$avg": "$quantity"},
                        "max_quantity": {"$max": "$quantity"}
                    }
                }
            ]
            
            avg_stocks = {item["_id"]: item["avg_quantity"] for item in self.db.inventory.aggregate(pipeline)}
            
            # Find items with stock > multiplier * average
            query = {}
            if location_type:
                query["location_type"] = location_type
            
            all_inventory = list(self.db.inventory.find(query))
            
            signals_generated = 0
            items_checked = 0
            
            for item in all_inventory:
                sku = item.get("sku")
                quantity = item.get("quantity", 0)
                avg_stock = avg_stocks.get(sku, 0)
                
                if avg_stock > 0:
                    items_checked += 1
                    overstock_threshold = avg_stock * multiplier
                    
                    if quantity > overstock_threshold:
                        location_id = item.get("location_id")
                        loc_type = item.get("location_type", "warehouse")
                        
                        # Get product name
                        product = self.db.products.find_one({"sku": sku})
                        product_name = product.get("name", sku) if product else sku
                        
                        signal = self.signal_service.create_signal(
                            signal_type=SignalType.OVERSTOCK,
                            entity_type=loc_type,
                            entity_id=location_id,
                            product_id=sku,
                            severity=SignalSeverity.LOW,
                            details={
                                "sku": sku,
                                "product_name": product_name,
                                "current_stock": quantity,
                                "normal_stock": round(avg_stock, 2),
                                "overstock_threshold": round(overstock_threshold, 2),
                                "excess_ratio": round(quantity / avg_stock, 2)
                            },
                            threshold={
                                "overstock_multiplier": multiplier,
                                "calculated_threshold": round(overstock_threshold, 2)
                            },
                            source=source
                        )
                        
                        if signal and signal.get("status") == "active":
                            signals_generated += 1
            
            result = {
                "detection_type": "overstock",
                "signals_generated": signals_generated,
                "items_checked": items_checked,
                "multiplier_used": multiplier,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Overstock detection complete: {signals_generated} signals "
                f"from {items_checked} items"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_overstock: {e}")
            raise
    
    # ========================================
    # DEMAND DETECTION FUNCTIONS
    # ========================================
    
    def detect_demand_spike(
        self,
        threshold: float = None,
        hours: int = 24,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect sudden increase in order volume (demand spike).
        
        Compares recent orders to historical average to identify
        unusual increases in demand.
        
        Args:
            threshold: Spike threshold multiplier (defaults to settings.demand_spike_threshold)
            hours: Time window for recent orders
            source: Source of detection
        
        Returns:
            Detection result with details
        """
        if threshold is None:
            threshold = settings.demand_spike_threshold
        
        try:
            now = datetime.utcnow()
            recent_start = now - timedelta(hours=hours)
            historical_start = now - timedelta(days=30)
            
            # Count recent orders
            recent_orders = self.db.orders.count_documents({
                "created_at": {"$gte": recent_start}
            })
            
            # Count historical average (per 24h period)
            historical_count = self.db.orders.count_documents({
                "created_at": {"$gte": historical_start, "$lt": recent_start}
            })
            
            days_in_historical = (now - historical_start).days
            avg_daily_orders = historical_count / max(days_in_historical, 1)
            avg_period_orders = avg_daily_orders * (hours / 24)
            
            signals_generated = 0
            spike_detected = False
            spike_factor = 0
            
            if avg_period_orders > 0:
                spike_factor = recent_orders / avg_period_orders
                
                if spike_factor >= threshold:
                    spike_detected = True
                    
                    signal = self.signal_service.create_signal(
                        signal_type=SignalType.DEMAND_SPIKE,
                        entity_type="order",
                        entity_id="system",
                        severity=SignalSeverity.HIGH,
                        details={
                            "current_orders": recent_orders,
                            "average_orders": round(avg_period_orders, 2),
                            "spike_factor": round(spike_factor, 2),
                            "time_window_hours": hours,
                            "historical_days": days_in_historical
                        },
                        threshold={
                            "demand_spike_threshold": threshold,
                            "time_window_hours": hours
                        },
                        source=source
                    )
                    
                    if signal and signal.get("status") == "active":
                        signals_generated += 1
            
            result = {
                "detection_type": "demand_spike",
                "signals_generated": signals_generated,
                "spike_detected": spike_detected,
                "current_orders": recent_orders,
                "average_orders": round(avg_period_orders, 2),
                "spike_factor": round(spike_factor, 2) if spike_factor else 0,
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Demand spike detection complete: spike_detected={spike_detected}, "
                f"factor={round(spike_factor, 2)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_demand_spike: {e}")
            raise
    
    def detect_demand_drop(
        self,
        threshold: float = None,
        hours: int = 24,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect sudden decrease in order volume (demand drop).
        
        Args:
            threshold: Drop threshold (defaults to settings.demand_drop_threshold)
            hours: Time window for recent orders
            source: Source of detection
        
        Returns:
            Detection result with details
        """
        if threshold is None:
            threshold = settings.demand_drop_threshold
        
        try:
            now = datetime.utcnow()
            recent_start = now - timedelta(hours=hours)
            historical_start = now - timedelta(days=30)
            
            # Count recent orders
            recent_orders = self.db.orders.count_documents({
                "created_at": {"$gte": recent_start}
            })
            
            # Count historical average
            historical_count = self.db.orders.count_documents({
                "created_at": {"$gte": historical_start, "$lt": recent_start}
            })
            
            days_in_historical = (now - historical_start).days
            avg_daily_orders = historical_count / max(days_in_historical, 1)
            avg_period_orders = avg_daily_orders * (hours / 24)
            
            signals_generated = 0
            drop_detected = False
            drop_factor = 1
            
            if avg_period_orders > 0:
                drop_factor = recent_orders / avg_period_orders
                
                if drop_factor <= threshold and avg_period_orders >= 5:  # Min orders to be significant
                    drop_detected = True
                    
                    signal = self.signal_service.create_signal(
                        signal_type=SignalType.DEMAND_DROP,
                        entity_type="order",
                        entity_id="system",
                        severity=SignalSeverity.MEDIUM,
                        details={
                            "current_orders": recent_orders,
                            "average_orders": round(avg_period_orders, 2),
                            "drop_factor": round(drop_factor, 2),
                            "time_window_hours": hours
                        },
                        threshold={
                            "demand_drop_threshold": threshold,
                            "time_window_hours": hours
                        },
                        source=source
                    )
                    
                    if signal and signal.get("status") == "active":
                        signals_generated += 1
            
            result = {
                "detection_type": "demand_drop",
                "signals_generated": signals_generated,
                "drop_detected": drop_detected,
                "current_orders": recent_orders,
                "average_orders": round(avg_period_orders, 2),
                "drop_factor": round(drop_factor, 2),
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Demand drop detection complete: drop_detected={drop_detected}, "
                f"factor={round(drop_factor, 2)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_demand_drop: {e}")
            raise
    
    # ========================================
    # DELIVERY DETECTION FUNCTIONS
    # ========================================
    
    def detect_delivery_delay(
        self,
        delay_hours: int = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect deliveries that are delayed beyond expected arrival time.
        
        Args:
            delay_hours: Minimum delay hours to trigger signal
            source: Source of detection
        
        Returns:
            Detection result with count of delayed deliveries
        """
        if delay_hours is None:
            delay_hours = settings.delivery_delay_hours
        
        try:
            now = datetime.utcnow()
            
            # Find in-transit deliveries that are past their expected arrival
            delayed_deliveries = list(self.db.deliveries.find({
                "status": "in_transit",
                "estimated_arrival": {"$lt": now}
            }))
            
            signals_generated = 0
            items_checked = len(delayed_deliveries)
            
            for delivery in delayed_deliveries:
                delivery_id = delivery.get("delivery_id")
                expected_arrival = delivery.get("estimated_arrival")
                
                if expected_arrival:
                    delay = now - expected_arrival
                    delay_hrs = delay.total_seconds() / 3600
                    
                    if delay_hrs >= delay_hours:
                        signal = self.signal_service.create_signal(
                            signal_type=SignalType.DELIVERY_DELAY,
                            entity_type="delivery",
                            entity_id=delivery_id,
                            details={
                                "delivery_id": delivery_id,
                                "order_id": delivery.get("order_id"),
                                "warehouse_id": delivery.get("warehouse_id"),
                                "store_id": delivery.get("store_id"),
                                "expected_arrival": expected_arrival.isoformat(),
                                "delay_hours": round(delay_hrs, 1),
                                "transport_mode": delivery.get("transport_mode"),
                                "distance_km": delivery.get("distance_km")
                            },
                            threshold={"delay_hours_threshold": delay_hours},
                            source=source
                        )
                        
                        if signal and signal.get("status") == "active":
                            signals_generated += 1
            
            result = {
                "detection_type": "delivery_delay",
                "signals_generated": signals_generated,
                "deliveries_checked": items_checked,
                "delay_threshold_hours": delay_hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Delivery delay detection complete: {signals_generated} delays "
                f"from {items_checked} in-transit deliveries"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_delivery_delay: {e}")
            raise
    
    # ========================================
    # WAREHOUSE UTILIZATION DETECTION
    # ========================================
    
    def detect_over_utilization(
        self,
        threshold: float = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect warehouses with utilization above threshold.
        
        Args:
            threshold: Over-utilization threshold percentage
            source: Source of detection
        
        Returns:
            Detection result with count of over-utilized warehouses
        """
        if threshold is None:
            threshold = settings.warehouse_over_utilization
        
        try:
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            
            signals_generated = 0
            items_checked = len(warehouses)
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get("warehouse_id")
                capacity = warehouse.get("capacity", 1)
                current = warehouse.get("current_utilization", 0)
                
                if capacity > 0:
                    utilization = (current / capacity) * 100
                    
                    if utilization >= threshold:
                        signal = self.signal_service.create_signal(
                            signal_type=SignalType.OVER_UTILIZATION,
                            entity_type="warehouse",
                            entity_id=warehouse_id,
                            details={
                                "warehouse_id": warehouse_id,
                                "warehouse_name": warehouse.get("name"),
                                "capacity": capacity,
                                "current_utilization": current,
                                "utilization_percent": round(utilization, 2),
                                "threshold": threshold,
                                "city": warehouse.get("location", {}).get("city")
                            },
                            threshold={"over_utilization_threshold": threshold},
                            source=source
                        )
                        
                        if signal and signal.get("status") == "active":
                            signals_generated += 1
            
            result = {
                "detection_type": "over_utilization",
                "signals_generated": signals_generated,
                "warehouses_checked": items_checked,
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Over-utilization detection complete: {signals_generated} signals "
                f"from {items_checked} warehouses"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_over_utilization: {e}")
            raise
    
    def detect_under_utilization(
        self,
        threshold: float = None,
        source: str = "scheduler"
    ) -> Dict[str, Any]:
        """
        Detect warehouses with utilization below threshold.
        
        Args:
            threshold: Under-utilization threshold percentage
            source: Source of detection
        
        Returns:
            Detection result with count of under-utilized warehouses
        """
        if threshold is None:
            threshold = settings.warehouse_under_utilization
        
        try:
            warehouses = list(self.db.warehouses.find({"is_active": True}))
            
            signals_generated = 0
            items_checked = len(warehouses)
            
            for warehouse in warehouses:
                warehouse_id = warehouse.get("warehouse_id")
                capacity = warehouse.get("capacity", 1)
                current = warehouse.get("current_utilization", 0)
                
                if capacity > 0:
                    utilization = (current / capacity) * 100
                    
                    if utilization <= threshold:
                        signal = self.signal_service.create_signal(
                            signal_type=SignalType.UNDER_UTILIZATION,
                            entity_type="warehouse",
                            entity_id=warehouse_id,
                            severity=SignalSeverity.LOW,
                            details={
                                "warehouse_id": warehouse_id,
                                "warehouse_name": warehouse.get("name"),
                                "capacity": capacity,
                                "current_utilization": current,
                                "utilization_percent": round(utilization, 2),
                                "threshold": threshold,
                                "city": warehouse.get("location", {}).get("city")
                            },
                            threshold={"under_utilization_threshold": threshold},
                            source=source
                        )
                        
                        if signal and signal.get("status") == "active":
                            signals_generated += 1
            
            result = {
                "detection_type": "under_utilization",
                "signals_generated": signals_generated,
                "warehouses_checked": items_checked,
                "threshold_used": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Under-utilization detection complete: {signals_generated} signals "
                f"from {items_checked} warehouses"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in detect_under_utilization: {e}")
            raise
    
    # ========================================
    # COMBINED DETECTION / BATCH OPERATIONS
    # ========================================
    
    def run_all_detections(self, source: str = "scheduler") -> Dict[str, Any]:
        """
        Run all detection functions.
        
        Returns:
            Combined results from all detections
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "detections": {}
        }
        
        # Inventory detections
        results["detections"]["low_stock"] = self.detect_low_stock(source=source)
        results["detections"]["stockout"] = self.detect_stockout(source=source)
        results["detections"]["overstock"] = self.detect_overstock(source=source)
        
        # Demand detections
        results["detections"]["demand_spike"] = self.detect_demand_spike(source=source)
        results["detections"]["demand_drop"] = self.detect_demand_drop(source=source)
        
        # Delivery detections
        results["detections"]["delivery_delay"] = self.detect_delivery_delay(source=source)
        
        # Warehouse detections
        results["detections"]["over_utilization"] = self.detect_over_utilization(source=source)
        results["detections"]["under_utilization"] = self.detect_under_utilization(source=source)
        
        # Summary
        total_signals = sum(
            d.get("signals_generated", 0) 
            for d in results["detections"].values()
        )
        results["total_signals_generated"] = total_signals
        
        logger.info(f"All detections complete: {total_signals} total signals generated")
        
        return results
    
    def check_inventory_health(self, sku: str, location_id: str) -> Dict[str, Any]:
        """
        Check inventory health for a specific SKU at a location.
        
        This is used for event-triggered checks after inventory updates.
        
        Returns:
            Health status and any signals generated
        """
        try:
            inventory = self.db.inventory.find_one({
                "sku": sku,
                "location_id": location_id
            })
            
            if not inventory:
                return {"status": "not_found", "signals": []}
            
            quantity = inventory.get("quantity", 0)
            reserved = inventory.get("reserved_stock", 0)
            available = quantity - reserved
            location_type = inventory.get("location_type", "warehouse")
            
            signals = []
            
            # Get product name
            product = self.db.products.find_one({"sku": sku})
            product_name = product.get("name", sku) if product else sku
            
            # Check for stockout
            if available <= 0:
                signal = self.signal_service.create_signal(
                    signal_type=SignalType.STOCKOUT,
                    entity_type=location_type,
                    entity_id=location_id,
                    product_id=sku,
                    severity=SignalSeverity.CRITICAL,
                    details={
                        "sku": sku,
                        "product_name": product_name,
                        "current_stock": quantity,
                        "reserved_stock": reserved,
                        "available_stock": available
                    },
                    source="event_trigger"
                )
                if signal:
                    signals.append(signal)
            
            # Check for low stock
            elif available < settings.low_stock_threshold:
                signal = self.signal_service.create_signal(
                    signal_type=SignalType.LOW_STOCK,
                    entity_type=location_type,
                    entity_id=location_id,
                    product_id=sku,
                    details={
                        "sku": sku,
                        "product_name": product_name,
                        "current_stock": quantity,
                        "reserved_stock": reserved,
                        "available_stock": available,
                        "threshold": settings.low_stock_threshold
                    },
                    threshold={"low_stock_threshold": settings.low_stock_threshold},
                    source="event_trigger"
                )
                if signal:
                    signals.append(signal)
            
            # If stock is healthy, resolve any existing signals
            else:
                self._resolve_inventory_signals(sku, location_id, available)
            
            return {
                "status": "checked",
                "sku": sku,
                "location_id": location_id,
                "available_stock": available,
                "signals_generated": len(signals),
                "signals": signals
            }
            
        except Exception as e:
            logger.error(f"Error checking inventory health: {e}")
            raise
    
    def _resolve_inventory_signals(
        self, 
        sku: str, 
        location_id: str, 
        current_stock: int
    ):
        """
        Auto-resolve LOW_STOCK and STOCKOUT signals when stock is replenished.
        """
        # Find active signals for this SKU/location
        active_signals = list(self.db.signals.find({
            "type": {"$in": [SignalType.LOW_STOCK, SignalType.STOCKOUT]},
            "entity_id": location_id,
            "product_id": sku,
            "status": "active"
        }))
        
        for signal in active_signals:
            self.signal_service.resolve_signal(
                signal["signal_id"],
                auto_resolved=True,
                action_taken={
                    "type": "stock_replenished",
                    "new_stock_level": current_stock
                },
                resolution_note=f"Stock replenished to {current_stock} units"
            )


# Global sensing service instance
sensing_service = SensingService()
