from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from database.db import get_db
from database.models import Supplier, PurchaseOrder
from agents.supplier_agent import SupplierAgent
from schemas.supplier_schema import *

router = APIRouter(prefix="/supplier", tags=["Supplier Agent"])


@router.post("/ask", response_model=AskResponse)
def ask_supplier_agent(request: AskRequest, db: Session = Depends(get_db)):
    """
    Ask a natural language question about suppliers.
    Powered by LangChain + OpenAI Tools agent with LSTM-enriched supplier data.

    Examples:
      - "Who should I buy 500 Circuit Boards from within 6 days?"
      - "Which supplier has the best reliability and quality?"
      - "What is the LSTM prediction for supplier 3?"
    """
    agent = SupplierAgent(db)
    result = agent.ask(
        question=request.question,
        api_key=request.openai_api_key or ""
    )
    return AskResponse(**result)

@router.post("/recommend", response_model=SupplierRecommendationResponse)
def recommend_suppliers(request: SupplierRecommendRequest, db: Session = Depends(get_db)):
    agent = SupplierAgent(db)
    return agent.recommend_suppliers(request)

@router.post("/search", response_model=ProductSearchResponse)
def search_suppliers_for_product(request: ProductSearchRequest, db: Session = Depends(get_db)):
    """
    Search for the best suppliers for a given product name.
    Returns top N suppliers (default 3) with full info: location, contact,
    reliability, quality, lead time, utility score, and past order history.
    """
    agent = SupplierAgent(db)
    top = agent.search_for_product(
        product=request.product,
        quantity=request.quantity,
        max_lead_time=request.max_lead_time_days,
        max_price=request.max_price_per_unit,
        top_n=request.top_n
    )
    if not top:
        raise HTTPException(status_code=404, detail=f"No suppliers found for '{request.product}'. Try a broader product name.")
    best = top[0]
    return ProductSearchResponse(
        product=request.product,
        quantity=request.quantity,
        top_suppliers=[SupplierFullInfo(**s) for s in top],
        best_supplier_name=best["supplier_name"],
        summary=(
            f"Best match: {best['supplier_name']} in {best['location']} "
            f"(Utility: {best['utility_score']}, Reliability: {best['reliability_score']}%, "
            f"Lead time: {best['estimated_lead_time_days']} days, "
            f"Est. cost for {request.quantity} units: ₹{best['estimated_total_cost']:,.2f})"
        )
    )

@router.get("/performance/{supplier_id}", response_model=PerformanceReport)
def get_performance(supplier_id: int, db: Session = Depends(get_db)):
    agent = SupplierAgent(db)
    return agent.get_performance_report(supplier_id)

@router.get("/list")
def list_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    return [
        {
            "id": s.id, "name": s.name, "location": s.location,
            "contact_info": s.contact_info, "specialties": s.specialties,
            "reliability_score": s.reliability_score,
            "avg_lead_time_days": s.avg_lead_time_days,
            "quality_rating": s.quality_rating
        }
        for s in suppliers
    ]

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """Return all unique product/item names from past purchase orders for autocomplete."""
    rows = db.query(distinct(PurchaseOrder.item_name)).order_by(PurchaseOrder.item_name).all()
    return {"products": [r[0] for r in rows if r[0]]}

@router.post("/update-metrics")
def update_metrics(db: Session = Depends(get_db)):
    agent = SupplierAgent(db)
    agent.update_supplier_metrics()
    return {"message": "Supplier metrics updated from past purchase order history."}

@router.post("/reset-reseed")
def reset_and_reseed(db: Session = Depends(get_db)):
    """
    Clears ALL supplier and order data and re-seeds fresh with
    15 suppliers and 300 purchase orders. Use after code changes to seed data.
    """
    agent = SupplierAgent.__new__(SupplierAgent)
    agent.db = db
    agent.weights = {"reliability": 0.40, "lead_time": 0.25, "quality": 0.20, "price": 0.15}
    return agent.reset_and_reseed()