from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import date

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    location = Column(String)
    contact_info = Column(String)
    specialties = Column(String)  # e.g. "electronics,components"
    avg_lead_time_days = Column(Float, default=10.0)
    reliability_score = Column(Float, default=85.0)  # 0-100
    quality_rating = Column(Float, default=4.5)     # 1-5

    orders = relationship("PurchaseOrder", back_populates="supplier")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    item_name = Column(String)
    quantity = Column(Integer)
    order_date = Column(Date)
    expected_delivery = Column(Date)
    actual_delivery = Column(Date, nullable=True)
    unit_price = Column(Float)
    quality_rating = Column(Float, nullable=True)  # 1-5
    status = Column(String, default="placed")
    review_comment = Column(Text, nullable=True)   # customer (our) review

    supplier = relationship("Supplier", back_populates="orders")