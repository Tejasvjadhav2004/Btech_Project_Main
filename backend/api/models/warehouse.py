"""
Pydantic models for Warehouse
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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


class Location(BaseModel):
    """Location model"""
    city: str
    state: Optional[str] = None
    country: str = "India"
    coordinates: Optional[Dict[str, float]] = None


class WarehouseBase(BaseModel):
    """Base Warehouse model"""
    warehouse_id: str = Field(..., description="Unique warehouse identifier")
    name: str = Field(..., description="Warehouse name")
    location: Location
    capacity: int = Field(..., description="Maximum storage capacity")
    current_utilization: int = Field(0, description="Current units stored")
    is_active: bool = Field(True, description="Warehouse active status")


class WarehouseCreate(WarehouseBase):
    """Model for creating a warehouse"""
    pass


class WarehouseUpdate(BaseModel):
    """Model for updating a warehouse"""
    name: Optional[str] = None
    location: Optional[Location] = None
    capacity: Optional[int] = None
    current_utilization: Optional[int] = None
    is_active: Optional[bool] = None
    efficiency_metrics: Optional[Dict[str, Any]] = None


class Warehouse(WarehouseBase):
    """Complete Warehouse model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    efficiency_metrics: Optional[Dict[str, Any]] = Field(None, description="Efficiency metrics for ML")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class WarehouseResponse(BaseModel):
    """Response model for Warehouse"""
    id: str
    warehouse_id: str
    name: str
    location: Location
    capacity: int
    current_utilization: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    efficiency_metrics: Optional[Dict[str, Any]]
