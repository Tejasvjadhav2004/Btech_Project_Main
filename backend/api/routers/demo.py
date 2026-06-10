"""
Demo Router - API endpoints for demo simulation control

Provides endpoints for:
- Starting/stopping simulation
- Switching between baseline and AI modes
- Triggering demo scenarios
- Getting live metrics
- WebSocket connections for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])

# Import services
from services.demo_simulation_service import demo_simulation_service, SimulationMode
from services.demo_metrics_service import demo_metrics_service


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for live updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._broadcast_task = None

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        message_json = json.dumps(message, default=str)

        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                self.disconnect(connection)

    async def start_broadcasts(self):
        """Start periodic broadcasts when simulation is running"""
        while True:
            try:
                if demo_simulation_service.state.is_running:
                    await self._broadcast_update()
                await asyncio.sleep(2)  # Broadcast every 2 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)

    async def _broadcast_update(self):
        """Broadcast current simulation state"""
        try:
            # Get metrics
            metrics = demo_metrics_service.get_metrics_for_display(
                demo_simulation_service.state.mode
            )

            # Get activity feed
            activities = demo_simulation_service.get_activity_feed(20)

            # Get simulation state
            state = demo_simulation_service._get_state()

            message = {
                "type": "simulation_update",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "state": state,
                    "metrics": metrics,
                    "activities": activities
                }
            }

            await self.broadcast(message)

        except Exception as e:
            logger.error(f"Error broadcasting update: {e}")


# Global connection manager
manager = ConnectionManager()


# ==================== REST API Endpoints ====================

@router.get("/status")
async def get_demo_status():
    """Get current demo simulation status"""
    return {
        "simulation": demo_simulation_service.get_status(),
        "metrics": demo_metrics_service.get_metrics_for_display()
    }


@router.post("/start")
async def start_demo(mode: str = "ai_autonomous"):
    """Start the demo simulation"""
    result = demo_simulation_service.start_simulation(mode)

    if result["success"]:
        # Start broadcasting updates
        demo_metrics_service.current_mode = mode

    return result


@router.post("/stop")
async def stop_demo():
    """Stop the demo simulation"""
    return demo_simulation_service.stop_simulation()


@router.post("/mode/{mode}")
async def set_demo_mode(mode: str):
    """Switch between baseline and AI autonomous modes"""
    valid_modes = ["baseline", "ai_autonomous"]

    if mode not in valid_modes:
        return {
            "success": False,
            "message": f"Invalid mode. Valid modes: {valid_modes}"
        }

    result = demo_simulation_service.set_mode(mode)

    if result["success"]:
        demo_metrics_service.current_mode = mode

        # Broadcast mode change
        await manager.broadcast({
            "type": "mode_changed",
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat()
        })

    return result


@router.post("/scenario/{scenario}")
async def trigger_scenario(scenario: str, params: Optional[Dict[str, Any]] = None):
    """Trigger a specific demo scenario"""
    result = demo_simulation_service.trigger_scenario(scenario, params or {})

    if result["success"]:
        # Broadcast scenario trigger
        await manager.broadcast({
            "type": "scenario_triggered",
            "scenario": scenario,
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        })

    return result


@router.get("/metrics")
async def get_demo_metrics(mode: Optional[str] = None):
    """Get current demo metrics"""
    return demo_metrics_service.get_metrics_for_display(mode)


@router.get("/metrics/comparison")
async def get_metrics_comparison():
    """Get comparison between baseline and AI modes"""
    return demo_metrics_service.get_comparison_summary()


@router.get("/metrics/history")
async def get_metrics_history(
    mode: str = "ai_autonomous",
    limit: int = Query(20, ge=1, le=100)
):
    """Get metrics history for a specific mode"""
    history = demo_metrics_service.metrics_history.get(mode, [])[-limit:]
    return {
        "mode": mode,
        "count": len(history),
        "history": history
    }


@router.get("/activities")
async def get_activities(limit: int = Query(50, ge=1, le=100)):
    """Get recent activities from the simulation"""
    return {
        "activities": demo_simulation_service.get_activity_feed(limit),
        "count": len(demo_simulation_service.activity_feed)
    }


@router.get("/activities/{activity_id}")
async def get_activity_detail(activity_id: str):
    """Get detailed information about a specific activity"""
    detail = demo_simulation_service.get_activity_detail(activity_id)

    if not detail:
        return {
            "success": False,
            "message": f"Activity {activity_id} not found"
        }

    return {
        "success": True,
        "activity": detail
    }


@router.get("/signals/active")
async def get_active_signals_detail():
    """Get detailed information about all active signals with AI analysis"""
    return {
        "signals": demo_simulation_service.get_active_signals_detail(),
        "count": len(demo_simulation_service.get_active_signals_detail())
    }


# ==================== Demo Control Endpoints ====================

@router.post("/reset")
async def reset_demo():
    """Reset the demo simulation state"""
    # Stop if running
    if demo_simulation_service.state.is_running:
        demo_simulation_service.stop_simulation()

    # Clear history
    demo_simulation_service.metrics_history = {
        "baseline": [],
        "ai_autonomous": []
    }
    demo_simulation_service.activity_feed = []
    demo_simulation_service.state = type(demo_simulation_service.state)()

    return {
        "success": True,
        "message": "Demo simulation reset"
    }


@router.post("/speed/{speed}")
async def set_simulation_speed(speed: float):
    """Set simulation speed multiplier"""
    if speed < 0.5 or speed > 5.0:
        return {
            "success": False,
            "message": "Speed must be between 0.5 and 5.0"
        }

    demo_simulation_service.state.speed_multiplier = speed

    return {
        "success": True,
        "speed": speed,
        "message": f"Simulation speed set to {speed}x"
    }


@router.post("/pause")
async def pause_simulation():
    """Pause the simulation"""
    demo_simulation_service.state.pause_simulation = True
    return {
        "success": True,
        "message": "Simulation paused"
    }


@router.post("/resume")
async def resume_simulation():
    """Resume a paused simulation"""
    demo_simulation_service.state.pause_simulation = False
    return {
        "success": True,
        "message": "Simulation resumed"
    }


# ==================== Scenarios Info ====================

@router.get("/scenarios")
async def get_scenarios():
    """Get list of available demo scenarios"""
    return {
        "scenarios": [
            {
                "id": "demand_spike",
                "name": "Demand Spike",
                "description": "Simulates sudden demand increase in a region",
                "expected_behavior": [
                    "Demand spike signal generated",
                    "Forecasting detects trend",
                    "Orchestration reallocates inventory",
                    "Stock balancing executed"
                ],
                "kpis_affected": ["stock_utilization", "stock_out_rate"]
            },
            {
                "id": "delivery_delay",
                "name": "Delivery Delay",
                "description": "Simulates transportation disruption",
                "expected_behavior": [
                    "Delivery delay signals generated",
                    "Route optimization triggered",
                    "Delivery rerouting executed",
                    "Priority escalation applied"
                ],
                "kpis_affected": ["avg_delay", "on_time_delivery"]
            },
            {
                "id": "inventory_crisis",
                "name": "Inventory Crisis",
                "description": "Simulates rapid stock depletion",
                "expected_behavior": [
                    "Low stock/stockout signals generated",
                    "Forecasting predicts depletion",
                    "Auto-replenishment workflow created",
                    "Redistribution executed"
                ],
                "kpis_affected": ["stock_out_rate", "response_time"]
            },
            {
                "id": "warehouse_overload",
                "name": "Warehouse Overload",
                "description": "Simulates warehouse capacity issues",
                "expected_behavior": [
                    "Over-utilization signal generated",
                    "Warehouse optimization triggered",
                    "Load redistribution executed",
                    "Balancing actions applied"
                ],
                "kpis_affected": ["stock_utilization"]
            }
        ]
    }


# ==================== WebSocket Endpoint ====================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time demo updates"""
    await manager.connect(websocket)

    try:
        # Start broadcast task if not running
        if manager._broadcast_task is None or manager._broadcast_task.done():
            manager._broadcast_task = asyncio.create_task(manager.start_broadcasts())

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for any message from client
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping/pong
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass

    finally:
        manager.disconnect(websocket)


# ==================== Initialize Demo Data ====================

@router.post("/initialize")
async def initialize_demo_data():
    """Initialize demo data if needed"""
    from db.connection import mongodb

    db = mongodb.get_database()

    # Check if we have enough data
    products_count = db.products.count_documents({})
    warehouses_count = db.warehouses.count_documents({})
    inventory_count = db.inventory.count_documents({})

    return {
        "status": "initialized",
        "data_available": {
            "products": products_count,
            "warehouses": warehouses_count,
            "inventory": inventory_count
        },
        "ready": products_count > 0 and warehouses_count > 0
    }
