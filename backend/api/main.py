"""
FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.connection import mongodb
from api.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Supply Chain Management API",
    description="API for Supply Chain Management System - Phase 7: LLM Orchestration Layer",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routers import products, warehouses, stores, inventory, dashboard, orders, deliveries, signals, forecast, predictions, orchestration, llm_orchestration, demo

logger.info("Registering routers...")
app.include_router(products.router)
app.include_router(warehouses.router)
app.include_router(stores.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)
app.include_router(orders.router)
app.include_router(deliveries.router)
logger.info(f"Registering signals router with prefix: {signals.router.prefix}")
app.include_router(signals.router)
app.include_router(forecast.router)
app.include_router(predictions.router)
logger.info("Registering orchestration router...")
app.include_router(orchestration.router)
logger.info("Registering LLM orchestration router...")
app.include_router(llm_orchestration.router)
logger.info("Registering demo router...")
app.include_router(demo.router)
logger.info("All routers registered successfully")


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and intelligence layer on startup"""
    logger.info("Starting Supply Chain Management API...")
    if mongodb.connect():
        logger.info("Database connection established")

        # Setup intelligence layer collections
        from db.collections import setup_intelligence_collections
        setup_intelligence_collections()
        logger.info("Intelligence layer collections initialized")

        # Setup LLM orchestration layer
        from services.llm_orchestrator_service import llm_orchestrator_service
        llm_orchestrator_service.setup_collections()
        logger.info("LLM Orchestration layer initialized")

        # Setup orchestration layer
        from orchestration.engine.orchestrator_service import orchestrator_service
        orchestrator_service.initialize()
        orchestrator_service.start()
        logger.info("Orchestration layer initialized and started")

        # Start the auto processor for automatic signal handling
        from orchestration.auto_processor import auto_processor
        auto_processor.start()
        logger.info("Auto Processor started - signals will be automatically orchestrated")

        # Start the background scheduler
        from services.scheduler_service import scheduler_service
        scheduler_service.start()
        logger.info("Background scheduler started")
    else:
        logger.error("Failed to establish database connection")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection and stop scheduler on shutdown"""
    logger.info("Shutting down Supply Chain Management API...")

    # Stop the auto processor
    from orchestration.auto_processor import auto_processor
    auto_processor.stop()
    logger.info("Auto Processor stopped")

    # Stop the background scheduler
    from services.scheduler_service import scheduler_service
    scheduler_service.stop()
    logger.info("Background scheduler stopped")

    mongodb.disconnect()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Supply Chain Management API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if mongodb.db else "disconnected"
    
    # Check scheduler status with error handling
    try:
        from services.scheduler_service import scheduler_service
        scheduler_status = scheduler_service.get_status()
        scheduler_info = {
            "running": scheduler_status["is_running"],
            "jobs": scheduler_status["job_count"]
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        scheduler_info = {
            "running": False,
            "jobs": 0,
            "error": str(e)
        }
    
    return {
        "status": "healthy",
        "database": db_status,
        "scheduler": scheduler_info,
        "version": "7.0.0",
        "phase": "LLM Orchestration Layer"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
