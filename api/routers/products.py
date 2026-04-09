"""
Products Router - Product API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from db.connection import get_db
from api.models.product import ProductResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get all products with optional filters"""
    db = get_db()
    query = {}
    
    if category:
        query["category"] = category
    if brand:
        query["brand"] = brand
    
    products = list(
        db.products.find(query)
        .skip(skip)
        .limit(limit)
    )
    
    # Convert ObjectId to string
    for product in products:
        product["id"] = str(product["_id"])
        del product["_id"]
    
    return products


@router.get("/{sku}", response_model=ProductResponse)
async def get_product(sku: str):
    """Get product by SKU"""
    db = get_db()
    product = db.products.find_one({"sku": sku})
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU {sku} not found")
    
    product["id"] = str(product["_id"])
    del product["_id"]
    
    return product
