from fastapi import FastAPI, Depends
from database.db import engine
from database import models
from api.supplier_routes import router as supplier_router
from api.inventory_routes import router as inventory_router
from api.security import verify_api_key

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Supplier Management System",
    description="Powered by LSTM + LangChain. All endpoints require X-API-Key header.",
    version="1.0.0",
)

# All routes under /supplier and /inventory are protected by API key
app.include_router(supplier_router,  dependencies=[Depends(verify_api_key)])
app.include_router(inventory_router, dependencies=[Depends(verify_api_key)])


@app.get("/", tags=["Health"])
def root():
    """Public health check — no API key required."""
    return {"status": "running", "message": "AI Supplier Management API is live."}
