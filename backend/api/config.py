"""
Configuration settings for the Supply Chain Management API
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
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
    dashboard_port: int = 5173
    
    # Data Configuration
    initial_inventory_state_path: str = os.path.join("data", "raw", "initial_inventory_state.csv")
    enhanced_supply_chain_data_path: str = os.path.join("data", "raw", "enhanced_supply_chain_data.csv")
    
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

    # Predictive Scheduler Intervals
    scheduler_demand_forecast_interval: int = 21600  # 6 hours
    scheduler_predictive_sensing_interval: int = 3600  # 1 hour

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

    # Store Types Configuration
    store_types: dict = {
        'Boutique': {'capacity_multiplier': 1.0},
        'Flagship': {'capacity_multiplier': 1.5},
        'Outlet': {'capacity_multiplier': 0.8}
    }

    # Warehouse-Region Mapping
    warehouse_regions: dict = {
        'WH001': 'West',
        'WH002': 'North',
        'WH003': 'South',
        'WH004': 'East',
        'WH005': 'South'
    }

    # Store-Region Mapping
    store_regions: dict = {
        'ST001': 'West', 'ST002': 'North', 'ST003': 'South',
        'ST004': 'East', 'ST005': 'South', 'ST006': 'South',
        'ST007': 'West', 'ST008': 'West'
    }

    # LLM API Keys (for orchestration)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # LLM Configuration
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
