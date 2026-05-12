"""
Pydantic models for Inventory
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


class InventoryBase(BaseModel):
    """Base Inventory model"""
    sku: str = Field(..., description="Reference to products.sku")
    location_id: str = Field(..., description="Reference to warehouse_id or store_id")
    location_type: str = Field(..., description="Location type: warehouse or store")
    quantity: int = Field(..., description="Current stock level")
    reserved_stock: int = Field(0, description="Stock reserved for pending orders")
    reorder_threshold: int = Field(20, description="Threshold for reorder alert")
    reorder_quantity: int = Field(50, description="Quantity to reorder")
    last_restocked: Optional[datetime] = None
    last_stock_check: Optional[datetime] = None


class InventoryCreate(InventoryBase):
    """Model for creating inventory"""
    pass


class InventoryUpdate(BaseModel):
    """Model for updating inventory"""
    quantity: Optional[int] = None
    reserved_stock: Optional[int] = None
    reorder_threshold: Optional[int] = None
    reorder_quantity: Optional[int] = None
    last_restocked: Optional[datetime] = None
    last_stock_check: Optional[datetime] = None
    stock_velocity: Optional[float] = None
    demand_trend: Optional[str] = None
    optimal_stock: Optional[int] = None
    lead_time_days: Optional[int] = None


class Inventory(InventoryBase):
    """Complete Inventory model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    stock_velocity: Optional[float] = Field(None, description="Units sold per day")
    demand_trend: Optional[str] = Field(None, description="Demand trend: increasing, stable, decreasing")
    optimal_stock: Optional[int] = Field(None, description="Optimal stock level")
    lead_time_days: Optional[int] = Field(None, description="Lead time in days")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class InventoryResponse(BaseModel):
    """Response model for Inventory"""
    id: str
    sku: str
    location_id: str
    location_type: str
    
    # Live tracking fields
    current_stock: int = Field(..., description="Current stock level (live)")
    available_stock: int = Field(..., description="Available stock (current - reserved)")
    reserved_stock: int = Field(0, description="Stock reserved for pending orders")
    initial_stock: int = Field(..., description="Initial stock from CSV")
    incoming_stock: int = Field(0, description="Stock in transit")
    damaged_stock: int = Field(0, description="Damaged goods")
    inventory_status: Optional[str] = Field(None, description="Inventory status indicator")
    
    # Transaction tracking
    transactions_count: int = Field(0, description="Total transactions processed")
    total_sales: int = Field(0, description="Total sales volume")
    total_restock: int = Field(0, description="Total restocks")
    last_updated: Optional[datetime] = None
    
    # Historical data (for ML)
    historical_avg_sales: Optional[int] = Field(None, description="Historical average sales from CSV")
    
    # Alert thresholds
    reorder_threshold: int
    reorder_quantity: int
    
    # Optimization fields
    optimal_stock: Optional[int] = None
    demand_trend: Optional[str] = None
    lead_time_days: Optional[int] = None
    
    # Legacy fields for compatibility
    quantity: int = Field(..., description="Legacy field (use current_stock)")
    last_restocked: Optional[datetime] = None
    last_stock_check: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    stock_velocity: Optional[float] = None
