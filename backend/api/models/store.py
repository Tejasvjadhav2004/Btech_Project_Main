"""
Pydantic models for Store
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .warehouse import Location


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


class StoreBase(BaseModel):
    """Base Store model"""
    store_id: str = Field(..., description="Unique store identifier")
    name: str = Field(..., description="Store name")
    location: Location
    store_type: Optional[str] = Field("Boutique", description="Store type")
    capacity: int = Field(..., description="Maximum display capacity")
    current_utilization: int = Field(0, description="Current units stored")
    is_active: bool = Field(True, description="Store active status")


class StoreCreate(StoreBase):
    """Model for creating a store"""
    pass


class StoreUpdate(BaseModel):
    """Model for updating a store"""
    name: Optional[str] = None
    location: Optional[Location] = None
    store_type: Optional[str] = None
    capacity: Optional[int] = None
    current_utilization: Optional[int] = None
    is_active: Optional[bool] = None
    customer_metrics: Optional[Dict[str, Any]] = None


class Store(StoreBase):
    """Complete Store model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    customer_metrics: Optional[Dict[str, Any]] = Field(None, description="Customer metrics for ML")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StoreResponse(BaseModel):
    """Response model for Store"""
    id: str
    store_id: str
    name: str
    location: Location
    store_type: Optional[str]
    capacity: int
    current_utilization: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    customer_metrics: Optional[Dict[str, Any]]
