"""
Pydantic models for Order
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


class OrderItem(BaseModel):
    """Order item model"""
    sku: str = Field(..., description="Product SKU")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: float = Field(..., description="Unit price")
    total_price: float = Field(..., description="Total price for this item")


class ShippingAddress(BaseModel):
    """Shipping address model"""
    city: str
    state: Optional[str] = None
    country: str = "India"


class OrderBase(BaseModel):
    """Base Order model"""
    order_id: str = Field(..., description="Unique order identifier")
    store_id: str = Field(..., description="Reference to store.store_id")
    items: List[OrderItem]
    total_amount: float = Field(..., description="Total order amount")
    status: str = Field("pending", description="Order status: pending, allocated, shipped, delivered, cancelled")
    priority: str = Field("normal", description="Order priority: high, normal, low")
    order_date: datetime
    expected_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    shipping_address: ShippingAddress
    assigned_warehouse: Optional[str] = Field(None, description="Assigned warehouse ID")
    delivery_id: Optional[str] = Field(None, description="Associated delivery ID")
    allocation_details: Optional[Dict[str, Any]] = Field(None, description="Inventory allocation details")


class OrderCreate(OrderBase):
    """Model for creating an order"""
    pass


class OrderUpdate(BaseModel):
    """Model for updating an order"""
    status: Optional[str] = None
    priority: Optional[str] = None
    expected_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    shipping_address: Optional[ShippingAddress] = None
    assigned_warehouse: Optional[str] = None
    delivery_id: Optional[str] = None
    allocation_details: Optional[Dict[str, Any]] = None
    fulfillment_priority: Optional[str] = None
    predicted_delay_risk: Optional[float] = None
    optimal_route: Optional[List[str]] = None


class Order(OrderBase):
    """Complete Order model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI/ML Future Fields
    fulfillment_priority: Optional[str] = Field(None, description="Fulfillment priority: high, medium, low")
    predicted_delay_risk: Optional[float] = Field(None, description="Predicted delay risk 0-1")
    optimal_route: Optional[List[str]] = Field(None, description="Optimal route for delivery")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class OrderResponse(BaseModel):
    """Response model for Order"""
    id: str
    order_id: str
    store_id: str
    items: List[OrderItem]
    total_amount: float
    status: str
    priority: Optional[str] = "normal"
    order_date: datetime
    expected_delivery: Optional[datetime]
    actual_delivery: Optional[datetime]
    shipping_address: ShippingAddress
    assigned_warehouse: Optional[str] = None
    delivery_id: Optional[str] = None
    allocation_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    fulfillment_priority: Optional[str]
    predicted_delay_risk: Optional[float]
    optimal_route: Optional[List[str]]
