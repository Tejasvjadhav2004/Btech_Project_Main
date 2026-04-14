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
    description="API for Supply Chain Management System - Phase 3: Sensing & Intelligence Layer",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routers import products, warehouses, stores, inventory, dashboard, orders, deliveries, signals, forecast

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
    
    # Check scheduler status
    from services.scheduler_service import scheduler_service
    scheduler_status = scheduler_service.get_status()
    
    return {
        "status": "healthy",
        "database": db_status,
        "scheduler": {
            "running": scheduler_status["is_running"],
            "jobs": scheduler_status["job_count"]
        },
        "version": "3.0.0",
        "phase": "Sensing & Intelligence Layer"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
