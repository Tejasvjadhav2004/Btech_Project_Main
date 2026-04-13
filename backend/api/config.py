"""
Configuration settings for the Supply Chain Management API
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB settings - MongoDB Atlas
    mongodb_uri: str = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_database_name: str = os.environ.get("MONGO_DB_NAME", "supply_chain_db")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Dashboard Configuration
    dashboard_host: str = "localhost"
    dashboard_port: int = 8501
    
    # Data Configuration
    supply_chain_data_path: str = "../data/raw/supply_chain_data.csv"
    fashion_boutique_data_path: str = "../data/raw/fashion_boutique_dataset.csv"
    
    # Monitoring Configuration
    low_stock_threshold: int = 10
    reorder_threshold: int = 5
    
    # Sensing & Intelligence Configuration
    critical_stock_threshold: int = 5
    overstock_multiplier: float = 3.0
    demand_spike_threshold: float = 2.0  # 2x normal orders
    demand_drop_threshold: float = 0.5   # 50% of normal orders
    delivery_delay_hours: int = 24
    warehouse_over_utilization: float = 90.0   # 90%
    warehouse_under_utilization: float = 20.0  # 20%
    
    # Scheduler Intervals (in SECONDS - recommended for production)
    # Low priority checks: once per hour
    scheduler_low_stock_interval: int = 3600          # 1 hour
    scheduler_stockout_interval: int = 1800         # 30 minutes (more critical)
    scheduler_delivery_delay_interval: int = 7200   # 2 hours
    scheduler_demand_analysis_interval: int = 14400 # 4 hours
    scheduler_utilization_interval: int = 3600      # 1 hour
    
    # Signal Configuration
    signal_auto_resolve_hours: int = 48  # Auto-resolve stale signals after 48 hours
    max_active_signals_per_entity: int = 10
    
    # Number of Warehouses and Stores to Generate
    num_warehouses: int = 5
    num_stores: int = 8
    
    # Warehouse Locations
    warehouse_cities: list = ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"]
    
    # Store Locations
    store_cities: list = [
        "Mumbai", "Delhi", "Bangalore", "Kolkata", 
        "Chennai", "Hyderabad", "Pune", "Ahmedabad"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
