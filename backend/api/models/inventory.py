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
    quantity: int
    reserved_stock: int = 0
    reorder_threshold: int
    reorder_quantity: int
    last_restocked: Optional[datetime]
    last_stock_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    stock_velocity: Optional[float]
    demand_trend: Optional[str]
    optimal_stock: Optional[int]
    lead_time_days: Optional[int]
