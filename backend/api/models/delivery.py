"""
Pydantic models for Delivery
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from enum import Enum


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


class DeliveryStatus(str, Enum):
    """Delivery status enum"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransportMode(str, Enum):
    """Transport mode enum"""
    TRUCK = "truck"
    AIR = "air"
    RAIL = "rail"
    EXPRESS = "express"


class RoutePoint(BaseModel):
    """Route point model"""
    location_id: str
    location_type: str  # warehouse, hub, store
    city: str
    coordinates: Optional[Dict[str, float]] = None
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None


class DeliveryBase(BaseModel):
    """Base Delivery model"""
    delivery_id: str = Field(..., description="Unique delivery identifier")
    order_id: str = Field(..., description="Reference to order.order_id")
    warehouse_id: str = Field(..., description="Source warehouse ID")
    store_id: str = Field(..., description="Destination store ID")
    status: DeliveryStatus = Field(DeliveryStatus.PENDING, description="Delivery status")
    transport_mode: TransportMode = Field(TransportMode.TRUCK, description="Transport mode")
    
    # Route information
    route: List[RoutePoint] = Field(default_factory=list, description="Delivery route points")
    distance_km: float = Field(0.0, description="Total distance in kilometers")
    
    # Time tracking
    estimated_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    estimated_duration_hours: float = Field(0.0, description="Estimated delivery duration in hours")
    
    # Additional details
    carrier: Optional[str] = Field(None, description="Carrier/logistics partner")
    tracking_number: Optional[str] = Field(None, description="External tracking number")
    notes: Optional[str] = None


class DeliveryCreate(BaseModel):
    """Model for creating a delivery"""
    order_id: str
    warehouse_id: str
    store_id: str
    transport_mode: Optional[TransportMode] = TransportMode.TRUCK
    carrier: Optional[str] = None
    notes: Optional[str] = None


class DeliveryUpdate(BaseModel):
    """Model for updating a delivery"""
    status: Optional[DeliveryStatus] = None
    transport_mode: Optional[TransportMode] = None
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class Delivery(DeliveryBase):
    """Complete Delivery model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class DeliveryResponse(BaseModel):
    """Response model for Delivery"""
    id: str
    delivery_id: str
    order_id: str
    warehouse_id: str
    store_id: str
    status: str
    transport_mode: str
    route: List[RoutePoint]
    distance_km: float
    estimated_departure: Optional[datetime]
    actual_departure: Optional[datetime]
    estimated_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    estimated_duration_hours: float
    carrier: Optional[str]
    tracking_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class DeliveryWithOrder(DeliveryResponse):
    """Delivery response with order details"""
    order_status: Optional[str] = None
    order_total: Optional[float] = None
    store_name: Optional[str] = None
    warehouse_name: Optional[str] = None
