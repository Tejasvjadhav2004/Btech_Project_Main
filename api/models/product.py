"""
Pydantic models for Product
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

    @classmethod
    def __get_pydantic_json_schema__(cls, _handler, _field=None):
        return {"type": "string"}


class ProductBase(BaseModel):
    """Base Product model"""
    sku: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    brand: str = Field(..., description="Brand name")
    product_type: Optional[str] = Field(None, description="Product type from supply chain data")
    original_price: float = Field(..., description="Original price")
    current_price: float = Field(..., description="Current price after markdown")
    average_rating: Optional[float] = Field(None, description="Customer rating")
    total_sales: int = Field(0, description="Total units sold")
    total_revenue: float = Field(0.0, description="Total revenue generated")
    is_active: bool = Field(True, description="Product availability status")


class ProductCreate(ProductBase):
    """Model for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Model for updating a product"""
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    original_price: Optional[float] = None
    current_price: Optional[float] = None
    average_rating: Optional[float] = None
    total_sales: Optional[int] = None
    total_revenue: Optional[float] = None
    is_active: Optional[bool] = None
    demand_forecast: Optional[Dict[str, Any]] = None
    optimization_score: Optional[float] = None
    tags: Optional[List[str]] = None


class Product(ProductBase):
    """Complete Product model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    demand_forecast: Optional[Dict[str, Any]] = Field(None, description="Demand forecast data")
    optimization_score: Optional[float] = Field(None, description="Optimization score for ML")
    tags: Optional[List[str]] = Field(None, description="Tags for ML categorization")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ProductResponse(BaseModel):
    """Response model for Product"""
    id: str
    sku: str
    name: str
    category: str
    brand: str
    product_type: Optional[str]
    original_price: float
    current_price: float
    average_rating: Optional[float]
    total_sales: int
    total_revenue: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    demand_forecast: Optional[Dict[str, Any]]
    optimization_score: Optional[float]
    tags: Optional[List[str]]
