from sqlalchemy.orm import Session
from agents.supplier_agent import SupplierAgent
from schemas.supplier_schema import ProductSearchRequest, ProductSearchResponse, SupplierFullInfo


class InventoryAgent:
    """
    Inventory Agent — monitors stock needs and queries the Supplier Agent
    to find the best suppliers for any required product.
    """

    def __init__(self, db: Session):
        self.db = db
        self.supplier_agent = SupplierAgent(db)

    def find_best_suppliers(
        self,
        product: str,
        quantity: int = 1,
        max_lead_time: int = None,
        max_price: float = None,
        top_n: int = 3,
    ) -> ProductSearchResponse:
        """
        Given a product name and required quantity, asks the Supplier Agent to
        rank the best matching suppliers and returns full details on top N.

        Usage example:
            agent = InventoryAgent(db)
            result = agent.find_best_suppliers("Circuit Board", quantity=200)
            print(result.best_supplier_name)
        """
        top = self.supplier_agent.search_for_product(
            product=product,
            quantity=quantity,
            max_lead_time=max_lead_time,
            max_price=max_price,
            top_n=top_n,
        )

        if not top:
            return ProductSearchResponse(
                product=product,
                quantity=quantity,
                top_suppliers=[],
                best_supplier_name="None",
                summary=f"No suppliers found for '{product}'. Try a broader keyword.",
            )

        best = top[0]
        return ProductSearchResponse(
            product=product,
            quantity=quantity,
            top_suppliers=[SupplierFullInfo(**s) for s in top],
            best_supplier_name=best["supplier_name"],
            summary=(
                f"Best match: {best['supplier_name']} in {best['location']} "
                f"(Utility: {best['utility_score']}, Reliability: {best['reliability_score']}%, "
                f"Lead time: {best['estimated_lead_time_days']} days, "
                f"Est. cost for {quantity} units: \u20b9{best['estimated_total_cost']:,.2f})"
            ),
        )
