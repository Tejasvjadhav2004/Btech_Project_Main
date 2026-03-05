from sqlalchemy.orm import Session
from database.models import Supplier, PurchaseOrder
from schemas.supplier_schema import *
from models.lstm_model import LSTMReliabilityPredictor
from datetime import datetime, timedelta
from typing import Optional
import random
import json

random.seed(42)  # reproducible generated data

# Maps product keywords → supplier specialty keywords for matching
PRODUCT_SPECIALTY_MAP = {
    "circuit board": ["electronics", "circuit boards"],
    "resistors": ["electronics", "resistors"],
    "capacitors": ["electronics", "capacitors"],
    "steel": ["steel", "raw materials"],
    "aluminium": ["raw materials", "aluminium"],
    "copper": ["raw materials", "copper"],
    "gear": ["mechanical parts", "gears"],
    "bearing": ["mechanical parts", "bearings"],
    "shaft": ["mechanical parts"],
    "plastic": ["plastic housing"],
    "rubber": ["rubber seals"],
    "motor": ["motors", "heavy parts"],
    "transformer": ["transformers", "heavy parts"],
    "machined": ["custom components", "machined parts"],
    "custom": ["custom components"],
    "component": ["electronics", "mechanical parts", "custom components"],
}

class SupplierAgent:
    def __init__(self, db: Session):
        self.db = db
        self.weights = {"reliability": 0.40, "lead_time": 0.25, "quality": 0.20, "price": 0.15}

        if self.db.query(Supplier).count() == 0:
            self._seed_historical_data()
            print("✅ Supplier Agent: Historical data seeded (15 suppliers, 300+ orders)")

        self.update_supplier_metrics()

    def _seed_historical_data(self):
        """Seed 15 realistic suppliers across India with 20 orders each (300 total orders)."""
        suppliers_data = [
            # name, location, contact, specialties, lead_time, reliability, quality, products, price_range
            ("Alpha Supplies Pvt Ltd",       "Mumbai, Maharashtra",        "sales@alphasupplies.in",    "electronics,raw materials",                5.2,  95.0, 4.7, ["Circuit Board", "Resistors Pack", "Aluminium Sheet"], (90, 150)),
            ("Beta Components Ltd",          "Delhi, Delhi",               "info@betacomponents.in",    "mechanical parts,gears,bearings",          7.5,  88.0, 4.4, ["Gear Set", "Ball Bearing", "Drive Shaft"],            (80, 130)),
            ("Pimpri Precision Parts",       "Pimpri, Maharashtra",        "orders@pimpriprecision.in", "custom components,machined parts",         3.8,  92.0, 4.6, ["Custom Part", "Machined Component"],                  (100, 160)),
            ("Gamma Industrial",             "Bangalore, Karnataka",       "supply@gammaindustrial.in", "electronics,circuit boards",               6.0,  91.0, 4.8, ["Circuit Board", "Capacitors Pack", "Resistors Pack"], (85, 145)),
            ("Delta Forge Works",            "Hyderabad, Telangana",       "delta@forgeworks.in",       "heavy parts,motors,transformers",          8.5,  85.0, 4.2, ["Motor Unit", "Transformer", "Steel Rod"],             (70, 140)),
            ("Zeta Electronics Hub",         "Chennai, Tamil Nadu",        "sales@zetaelectronics.in",  "electronics,circuit boards,capacitors",    5.5,  93.0, 4.9, ["Circuit Board", "Capacitors Pack", "Resistors Pack"], (95, 155)),
            ("Eta Raw Materials Co",         "Pune, Maharashtra",          "eta@rawmaterials.in",       "raw materials,copper,aluminium,steel",     4.0,  89.0, 4.3, ["Aluminium Sheet", "Copper Wire", "Steel Rod"],        (55, 110)),
            ("Theta Mechanical Works",       "Nashik, Maharashtra",        "theta@mechanical.in",       "mechanical parts,gears,bearings,shafts",   5.0,  87.0, 4.5, ["Gear Set", "Ball Bearing", "Drive Shaft"],            (75, 130)),
            ("Iota Plastics & Packaging",    "Ahmedabad, Gujarat",         "iota@plastics.in",          "plastic housing,rubber seals,packaging",   4.5,  90.0, 4.4, ["Plastic Housing", "Rubber Seal"],                     (45, 100)),
            ("Kappa Motors & Drives",        "Coimbatore, Tamil Nadu",     "kappa@motordrives.in",      "motors,transformers,heavy parts",          9.0,  86.0, 4.6, ["Motor Unit", "Transformer"],                          (110, 210)),
            ("Lambda Steel Industries",      "Jamshedpur, Jharkhand",      "lambda@steelindustries.in", "steel,raw materials,heavy metals",         6.5,  94.0, 4.5, ["Steel Rod", "Aluminium Sheet", "Copper Wire"],        (50, 100)),
            ("Mu Precision Engineering",     "Surat, Gujarat",             "mu@precisioneng.in",        "custom components,machined parts,cnc",     4.2,  91.0, 4.7, ["Machined Component", "Custom Part"],                  (95, 165)),
            ("Nu Electronics & Systems",     "Noida, Uttar Pradesh",       "nu@electronicssys.in",      "electronics,resistors,capacitors,pcb",     5.8,  89.0, 4.5, ["Resistors Pack", "Capacitors Pack", "Circuit Board"], (80, 140)),
            ("Xi Rubber & Polymer Works",    "Kolkata, West Bengal",       "xi@rubberpolymer.in",       "rubber seals,plastic housing,gaskets",     6.0,  82.0, 4.1, ["Rubber Seal", "Plastic Housing"],                     (40, 90)),
            ("Omicron Heavy Industries",     "Visakhapatnam, Andhra Pradesh","omicron@heavyind.in",     "heavy parts,motors,transformers,forgings", 10.0, 83.0, 4.3, ["Motor Unit", "Transformer", "Heavy Gear"],            (100, 190)),
        ]

        review_pool = [
            "Excellent quality and on-time delivery. Will order again.",
            "Minor delay but product quality exceeded expectations.",
            "Perfect service, competitive pricing from local supplier.",
            "Delivery was 2 days late due to transport, but overall satisfied.",
            "High quality materials, reliable long-term partner.",
            "Good communication, price could be slightly better.",
            "Fast delivery, great for urgent needs.",
            "Consistent performance over the last year.",
            "Products met spec exactly, packaging was also good.",
            "Slightly expensive but never compromises on quality.",
            "Great after-sales support. Will continue partnership.",
            "Quick response to queries and smooth logistics.",
            "One batch had minor defects but quickly replaced.",
            "Best pricing in the region for this product category.",
            "Reliable vendor, always delivers as promised.",
            "Product quality is top-notch, very satisfied.",
            "Smooth ordering process. Invoices are always accurate.",
            "Would appreciate faster lead times but quality is superb.",
            "Recommended by our QC team as preferred vendor.",
            "Always meets deadlines, great coordination with our team.",
        ]

        for (name, location, contact, specialties, lead_time, reliability, quality, products, price_range) in suppliers_data:
            sup = Supplier(
                name=name, location=location, contact_info=contact,
                specialties=specialties, avg_lead_time_days=lead_time,
                reliability_score=reliability, quality_rating=quality
            )
            self.db.add(sup)
            self.db.commit()
            self.db.refresh(sup)

            # 20 orders per supplier across their product list
            for i in range(20):
                item = products[i % len(products)]
                order_date = datetime.utcnow().date() - timedelta(days=random.randint(10, 900))
                expected = order_date + timedelta(days=int(lead_time))
                actual_days = max(1, int(lead_time + random.gauss(0, 2.5)))
                actual_delivery = order_date + timedelta(days=actual_days)
                q = round(max(1.0, min(5.0, quality + random.gauss(0, 0.35))), 1)
                price_min, price_max = price_range
                po = PurchaseOrder(
                    supplier_id=sup.id,
                    item_name=item,
                    quantity=random.randint(50, 600),
                    order_date=order_date,
                    expected_delivery=expected,
                    actual_delivery=actual_delivery,
                    unit_price=round(random.uniform(price_min, price_max), 2),
                    quality_rating=q,
                    status="delivered",
                    review_comment=random.choice(review_pool)
                )
                self.db.add(po)
            self.db.commit()

    def reset_and_reseed(self):
        """Delete all existing data and re-seed fresh. Call via /supplier/reset-reseed endpoint."""
        self.db.query(PurchaseOrder).delete()
        self.db.query(Supplier).delete()
        self.db.commit()
        self._seed_historical_data()
        self.update_supplier_metrics()
        return {"message": "Database reset and re-seeded with 15 suppliers and 300 orders."}

    def update_supplier_metrics(self):
        """Recalculates reliability score from actual purchase history — keeps the model current."""
        suppliers = self.db.query(Supplier).all()
        for sup in suppliers:
            orders = sup.orders
            if len(orders) > 3:
                otd = sum(1 for o in orders if o.actual_delivery and (o.actual_delivery - o.expected_delivery).days <= 3) / len(orders) * 100
                avg_q = sum(o.quality_rating or 4.0 for o in orders) / len(orders)
                sup.reliability_score = round(0.6 * otd + 0.4 * (avg_q * 20), 1)
        self.db.commit()

    # ── LSTM Predictor ────────────────────────────────────────────────────────────

    def _lstm_predict(self, supplier: Supplier) -> Optional[float]:
        """
        Train a fresh LSTMReliabilityPredictor on this supplier's order history
        and return the predicted next-period reliability (0–100), or None if
        there is not enough data (< 5 orders needed).
        """
        predictor = LSTMReliabilityPredictor()
        return predictor.predict_reliability(supplier.orders)

    # ── Utility + LSTM Blended Score ──────────────────────────────────────────────

    def _compute_utility(self, supplier: Supplier, req: SupplierRecommendRequest, avg_price: float) -> float:
        lead_score = max(0, (req.max_lead_time_days or 30 - supplier.avg_lead_time_days) / 30) if req.max_lead_time_days else 0.8
        price_score = max(0, (req.max_price_per_unit or 200 - avg_price) / 200) if req.max_price_per_unit else 0.7
        utility = (
            self.weights["reliability"] * (supplier.reliability_score / 100) +
            self.weights["lead_time"] * lead_score +
            self.weights["quality"] * (supplier.quality_rating / 5) +
            self.weights["price"] * price_score
        )
        return round(utility * 100, 1)

    def _compute_final_score(
        self, supplier: Supplier, req: SupplierRecommendRequest, avg_price: float
    ) -> tuple:
        """
        Blends the rule-based Utility score with the LSTM-predicted reliability.
        Returns (final_score, lstm_prediction)
          - If LSTM has enough data:  final = 0.70 * utility + 0.30 * lstm
          - Otherwise:                final = utility  (pure rule-based fallback)
        """
        utility   = self._compute_utility(supplier, req, avg_price)
        lstm_pred = self._lstm_predict(supplier)

        if lstm_pred is not None:
            # Weight: 70% traditional utility model, 30% LSTM deep learning
            final = round(0.70 * utility + 0.30 * lstm_pred, 1)
        else:
            final = utility

        return final, lstm_pred

    def recommend_suppliers(self, req: SupplierRecommendRequest) -> SupplierRecommendationResponse:
        """
        Main AI decision engine.
        Scoring = 70% Weighted Utility Model + 30% LSTM Deep Learning prediction.
        """
        suppliers  = self.db.query(Supplier).all()
        candidates = []

        for sup in suppliers:
            recent_orders = [o for o in sup.orders if o.item_name == req.item_name][-5:]
            avg_price     = sum(o.unit_price for o in recent_orders) / len(recent_orders) if recent_orders else 120.0

            score, lstm_pred = self._compute_final_score(sup, req, avg_price)
            est_cost = round(avg_price * req.quantity, 2)
            est_lead = int(sup.avg_lead_time_days)

            rationale = f"Reliability: {sup.reliability_score}%. "
            if lstm_pred is not None:
                trend = (
                    "LSTM predicts improvement" if lstm_pred > sup.reliability_score
                    else "LSTM predicts decline" if lstm_pred < sup.reliability_score - 5
                    else "LSTM predicts stable performance"
                )
                rationale += f"{trend} (predicted: {lstm_pred}%). "
            if est_lead <= (req.max_lead_time_days or 30):
                rationale += "Meets lead-time constraint. "
            if "Maharashtra" in sup.location:
                rationale += "Local Maharashtra supplier — faster logistics."

            candidates.append(Recommendation(
                supplier_id=sup.id,
                supplier_name=sup.name,
                utility_score=score,
                estimated_total_cost=est_cost,
                estimated_lead_time=est_lead,
                rationale=rationale
            ))

        candidates.sort(key=lambda x: x.utility_score, reverse=True)
        return SupplierRecommendationResponse(
            recommendations=candidates[:5],
            best_choice=candidates[0] if candidates else None
        )

    def search_for_product(self, product: str, quantity: int = 1,
                           max_lead_time: int = None, max_price: float = None,
                           top_n: int = 3) -> list:
        """
        AI product search: given a product name, find the best matching suppliers.
        Matches by:  1) past purchase history for that product
                     2) supplier specialty keywords
        Returns top_n suppliers sorted by utility score with full info.
        """
        product_lower = product.lower()

        # Extract search keywords from the product name
        search_keywords = [kw for kw in product_lower.split() if len(kw) > 2]
        # Also check PRODUCT_SPECIALTY_MAP for mapped specialty terms
        mapped_specialties = []
        for key, specs in PRODUCT_SPECIALTY_MAP.items():
            if key in product_lower or any(kw in product_lower for kw in key.split()):
                mapped_specialties.extend(specs)

        suppliers = self.db.query(Supplier).all()
        results = []

        for sup in suppliers:
            specialties_lower = (sup.specialties or "").lower()

            # Check purchase history match (partial name match)
            product_orders = [
                o for o in sup.orders
                if any(kw in (o.item_name or "").lower() for kw in search_keywords)
                or product_lower in (o.item_name or "").lower()
            ]
            has_history = len(product_orders) > 0

            # Check specialty keyword match
            specialty_match = (
                any(kw in specialties_lower for kw in search_keywords) or
                any(spec in specialties_lower for spec in mapped_specialties)
            )

            if not has_history and not specialty_match:
                continue  # skip irrelevant suppliers

            # Average price from matched orders, else from all orders, else default
            avg_price = (
                sum(o.unit_price for o in product_orders) / len(product_orders)
                if product_orders else
                sum(o.unit_price for o in sup.orders[-10:]) / max(len(sup.orders[-10:]), 1)
            )

            req = SupplierRecommendRequest(
                item_name=product,
                quantity=quantity,
                max_lead_time_days=max_lead_time,
                max_price_per_unit=max_price
            )
            score, lstm_pred = self._compute_final_score(sup, req, avg_price)
            est_cost = round(avg_price * quantity, 2)

            # Build rationale
            rationale_parts = [f"Reliability: {sup.reliability_score}%."]
            rationale_parts.append(f"Lead time: {int(sup.avg_lead_time_days)} days.")
            rationale_parts.append(f"Quality rating: {sup.quality_rating}/5.")
            if lstm_pred is not None:
                trend = (
                    "LSTM: improving trend" if lstm_pred > sup.reliability_score
                    else "LSTM: declining trend" if lstm_pred < sup.reliability_score - 5
                    else "LSTM: stable trend"
                )
                rationale_parts.append(f"{trend} (predicted reliability: {lstm_pred}%).")
            if has_history:
                rationale_parts.append(f"Supplied this product {len(product_orders)} time(s) before.")
            if specialty_match:
                rationale_parts.append(f"Specializes in: {sup.specialties}.")
            if "Maharashtra" in sup.location:
                rationale_parts.append("Local Maharashtra supplier — faster logistics.")

            results.append({
                "supplier_id": sup.id,
                "supplier_name": sup.name,
                "location": sup.location,
                "contact_info": sup.contact_info,
                "specialties": sup.specialties,
                "avg_lead_time_days": sup.avg_lead_time_days,
                "reliability_score": sup.reliability_score,
                "quality_rating": sup.quality_rating,
                "utility_score": score,
                "estimated_total_cost": est_cost,
                "estimated_lead_time_days": int(sup.avg_lead_time_days),
                "past_orders_for_product": len(product_orders),
                "rationale": " ".join(rationale_parts),
            })

        results.sort(key=lambda x: x["utility_score"], reverse=True)
        return results[:top_n]

    def get_performance_report(self, supplier_id: int) -> PerformanceReport:
        """Graphs + customer reviews of past data."""
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise ValueError("Supplier not found")

        orders = sorted(supplier.orders, key=lambda o: o.order_date)
        total = len(orders)
        otd_rate = sum(1 for o in orders if o.actual_delivery and (o.actual_delivery - o.expected_delivery).days <= 3) / total * 100 if total else 0
        avg_quality = sum(o.quality_rating or 4 for o in orders) / total if total else 0

        # Graph data (ready for Chart.js)
        months = [o.order_date.strftime("%Y-%m") for o in orders[-12:]]
        otd_rates = [100 if o.actual_delivery and (o.actual_delivery - o.expected_delivery).days <= 3 else 70 for o in orders[-12:]]
        quality_scores = [o.quality_rating or 4.0 for o in orders[-12:]]
        avg_prices = [o.unit_price for o in orders[-12:]]

        reviews = [{"date": o.order_date.strftime("%Y-%m"), "rating": o.quality_rating or 4.0, "comment": o.review_comment} for o in orders[-5:] if o.review_comment]

        return PerformanceReport(
            supplier={"id": supplier.id, "name": supplier.name, "location": supplier.location},
            total_orders=total,
            on_time_delivery_rate=round(otd_rate, 1),
            avg_quality=round(avg_quality, 1),
            graph_data=GraphData(months=months, otd_rates=otd_rates, quality_scores=quality_scores, avg_prices=avg_prices),
            recent_reviews=reviews
        )

    # ── LangChain Tools ─────────────────────────────────────────────────────────────

    def _build_langchain_tools(self) -> list:
        """
        Returns a list of LangChain Tool objects that wrap this agent’s methods.
        The tools are used by the LangChain ReAct agent to answer natural language
        procurement questions.
        """
        from langchain.tools import tool

        @tool
        def list_all_suppliers(query: str = "") -> str:
            """List all available suppliers with their key metrics (name, location, specialties, reliability, quality, lead time)."""
            suppliers = self.db.query(Supplier).all()
            return json.dumps([
                {
                    "id": s.id, "name": s.name, "location": s.location,
                    "specialties": s.specialties,
                    "reliability_score": s.reliability_score,
                    "avg_lead_time_days": s.avg_lead_time_days,
                    "quality_rating": s.quality_rating
                } for s in suppliers
            ], indent=2)

        @tool
        def get_supplier_performance(supplier_id: str) -> str:
            """Get detailed performance report and customer reviews for a supplier. Input: supplier_id as integer string."""
            try:
                report = self.get_performance_report(int(supplier_id))
                return json.dumps({
                    "supplier": report.supplier,
                    "total_orders": report.total_orders,
                    "on_time_delivery_rate": report.on_time_delivery_rate,
                    "avg_quality": report.avg_quality,
                    "recent_reviews": report.recent_reviews
                }, indent=2)
            except Exception as e:
                return f"Error: {e}"

        @tool
        def predict_supplier_reliability_lstm(supplier_id: str) -> str:
            """Predict a supplier's future reliability using LSTM deep learning. Input: supplier_id as integer string."""
            sup = self.db.query(Supplier).filter(Supplier.id == int(supplier_id)).first()
            if not sup:
                return "Supplier not found"
            lstm_pred = self._lstm_predict(sup)
            if lstm_pred is None:
                return json.dumps({"supplier_name": sup.name, "lstm_prediction": None,
                                   "note": "Not enough order history for LSTM (need 5+ orders)"})
            trend = (
                "Improving" if lstm_pred > sup.reliability_score
                else "Declining" if lstm_pred < sup.reliability_score - 5
                else "Stable"
            )
            return json.dumps({
                "supplier_id": sup.id, "supplier_name": sup.name,
                "current_reliability": sup.reliability_score,
                "lstm_predicted_reliability": lstm_pred,
                "trend": trend
            }, indent=2)

        @tool
        def recommend_suppliers_for_item(params_json: str) -> str:
            """Rank suppliers for a procurement request. Input: JSON string with keys: item_name (str), quantity (int), max_lead_time_days (int or null), max_price_per_unit (float or null)."""
            try:
                params = json.loads(params_json)
                req    = SupplierRecommendRequest(**params)
                result = self.recommend_suppliers(req)
                return json.dumps({
                    "best_choice": result.best_choice.dict() if result.best_choice else None,
                    "top_5": [r.dict() for r in result.recommendations]
                }, indent=2)
            except Exception as e:
                return f"Error: {e}"

        return [
            list_all_suppliers,
            get_supplier_performance,
            predict_supplier_reliability_lstm,
            recommend_suppliers_for_item,
        ]

    # ── Natural Language Ask (LangChain ReAct Agent) ────────────────────────────

    def ask(self, question: str, api_key: str = "") -> dict:
        """
        Answer a natural language procurement question using the LangChain
        OpenAI-Tools agent with our custom supplier tools.

        Requires OPENAI_API_KEY in .env or passed explicitly.
        """
        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import HumanMessage
        from config import settings

        key = api_key or settings.OPENAI_API_KEY
        if not key:
            return {
                "answer": (
                    "⚠️ No OpenAI API key configured. "
                    "Set OPENAI_API_KEY in your .env file or pass it in the request body."
                ),
                "tools_used": [],
            }

        tools = self._build_langchain_tools()
        llm   = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0, api_key=key)

        system_prompt = (
            "You are an expert AI procurement assistant for an Indian manufacturing company. "
            "Use the available tools to answer questions about suppliers. "
            "Always include supplier names, reliability scores, lead times, and estimated costs. "
            "Use INR (₹) for prices. Be concise and structured in your responses."
        )

        agent  = create_react_agent(llm, tools, prompt=system_prompt)
        tool_names = [t.name for t in tools]
        try:
            result = agent.invoke({"messages": [HumanMessage(content=question)]})
            answer = result["messages"][-1].content
        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "insufficient_quota" in err.lower() or "429" in err:
                answer = (
                    "⚠️ OpenAI quota exceeded. Your API key has run out of credits. "
                    "Please top up your OpenAI account at https://platform.openai.com/account/billing"
                )
            elif "auth" in err.lower() or "401" in err or "invalid" in err.lower():
                answer = (
                    "❌ Invalid OpenAI API key. "
                    "Please update OPENAI_API_KEY in your .env file."
                )
            else:
                answer = f"❌ Agent error: {err[:300]}"
        return {"answer": answer, "tools_used": tool_names}
