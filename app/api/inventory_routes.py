from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database.db import get_db
from agents.invetory_agent import InventoryAgent
from schemas.supplier_schema import ProductSearchResponse

router = APIRouter(prefix="/inventory", tags=["Inventory Agent"])


@router.get("/find-supplier", response_model=ProductSearchResponse)
def find_supplier_for_product(
    product: str,
    quantity: int = 1,
    max_lead_time_days: Optional[int] = None,
    max_price_per_unit: Optional[float] = None,
    top_n: int = 3,
    db: Session = Depends(get_db),
):
    """
    Inventory Agent endpoint — search for the best suppliers for any product.

    Examples:
      GET /inventory/find-supplier?product=Circuit+Board&quantity=200
      GET /inventory/find-supplier?product=Motor+Unit&quantity=50&max_lead_time_days=7
      GET /inventory/find-supplier?product=Steel+Rod&quantity=1000&max_price_per_unit=80

    Returns top N suppliers (default 3) ranked by utility score with:
      - Supplier name, location, contact info
      - Reliability score, quality rating, lead time
      - Estimated total cost for requested quantity
      - Past order history count for this product
      - Rationale explaining why each supplier is recommended
    """
    agent = InventoryAgent(db)
    result = agent.find_best_suppliers(
        product=product,
        quantity=quantity,
        max_lead_time=max_lead_time_days,
        max_price=max_price_per_unit,
        top_n=top_n,
    )
    if not result.top_suppliers:
        raise HTTPException(
            status_code=404,
            detail=f"No suppliers found for '{product}'. Try a broader keyword (e.g. 'electronics', 'motor', 'steel').",
        )
    return result
