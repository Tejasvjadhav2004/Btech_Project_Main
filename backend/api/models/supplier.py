"""
Pydantic models for Supplier
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
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


class Contact(BaseModel):
    """Contact information model"""
    email: Optional[str] = None
    phone: Optional[str] = None


class SupplierBase(BaseModel):
    """Base Supplier model"""
    supplier_id: str = Field(..., description="Unique supplier identifier")
    name: str = Field(..., description="Supplier name")
    location: Dict[str, str] = Field(..., description="Location information")
    contact: Optional[Contact] = None
    products_supplied: List[str] = Field(default_factory=list, description="List of SKUs")
    lead_time_days: int = Field(7, description="Average lead time in days")
    reliability_score: float = Field(0.8, description="Reliability score 0-1")
    is_active: bool = Field(True, description="Supplier active status")


class SupplierCreate(SupplierBase):
    """Model for creating a supplier"""
    pass


class SupplierUpdate(BaseModel):
    """Model for updating a supplier"""
    name: Optional[str] = None
    location: Optional[Dict[str, str]] = None
    contact: Optional[Contact] = None
    products_supplied: Optional[List[str]] = None
    lead_time_days: Optional[int] = None
    reliability_score: Optional[float] = None
    is_active: Optional[bool] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class Supplier(SupplierBase):
    """Complete Supplier model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics for ML")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SupplierResponse(BaseModel):
    """Response model for Supplier"""
    id: str
    supplier_id: str
    name: str
    location: Dict[str, str]
    contact: Optional[Contact]
    products_supplied: List[str]
    lead_time_days: int
    reliability_score: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    performance_metrics: Optional[Dict[str, Any]]
