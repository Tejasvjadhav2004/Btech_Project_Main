from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date

class SupplierRecommendRequest(BaseModel):
    item_name: str
    quantity: int
    max_lead_time_days: Optional[int] = None
    max_price_per_unit: Optional[float] = None
    priority: str = "balanced"  # balanced, cost, speed, quality

class Recommendation(BaseModel):
    supplier_id: int
    supplier_name: str
    utility_score: float
    estimated_total_cost: float
    estimated_lead_time: int
    rationale: str

class SupplierRecommendationResponse(BaseModel):
    recommendations: List[Recommendation]
    best_choice: Recommendation

class GraphData(BaseModel):
    months: List[str]
    otd_rates: List[float]          # On-Time Delivery %
    quality_scores: List[float]
    avg_prices: List[float]

class PerformanceReport(BaseModel):
    supplier: Dict
    total_orders: int
    on_time_delivery_rate: float
    avg_quality: float
    graph_data: GraphData
    recent_reviews: List[Dict]   # {"date": "2025-01", "rating": 4.7, "comment": "..."}

# ── Product Search Schemas ──────────────────────────────────────────────────

class ProductSearchRequest(BaseModel):
    product: str                          # e.g. "Circuit Board", "Motor Unit"
    quantity: int = 1
    max_lead_time_days: Optional[int] = None
    max_price_per_unit: Optional[float] = None
    top_n: int = 3                        # how many top suppliers to return

class SupplierFullInfo(BaseModel):
    supplier_id: int
    supplier_name: str
    location: str
    contact_info: str
    specialties: str
    avg_lead_time_days: float
    reliability_score: float
    quality_rating: float
    utility_score: float
    estimated_total_cost: float
    estimated_lead_time_days: int
    past_orders_for_product: int
    rationale: str

class ProductSearchResponse(BaseModel):
    product: str
    quantity: int
    best_supplier_name: str
    summary: str
    top_suppliers: List[SupplierFullInfo]


# ── LangChain Natural Language Ask Schemas ───────────────────────────────

class AskRequest(BaseModel):
    question: str                          # natural language question
    openai_api_key: Optional[str] = None  # optional override; uses .env if absent

class AskResponse(BaseModel):
    answer: str
    tools_used: List[str] = []