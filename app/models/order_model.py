import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


class LineItemDetail(BaseModel):
    item_id: int
    name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderDetailResponse(BaseModel):
    order_id: int
    status: str
    created_at: datetime
    items: List[LineItemDetail]
    total_price: Decimal

    class Config:
        schema_extra = {
            "example": {
                "order_id": 123,
                "status": "created",
                "created_at": "2025-03-20T14:30:00",
                "items": [
                    {
                        "item_id": 1,
                        "name": "Product A",
                        "quantity": 2,
                        "unit_price": 24.99,
                        "subtotal": 49.98,
                    },
                    {
                        "item_id": 3,
                        "name": "Product C",
                        "quantity": 1,
                        "unit_price": 9.99,
                        "subtotal": 9.99,
                    },
                ],
                "total_price": 59.97,
            }
        }


class ShippingInfo(BaseModel):
    carrier: str = Field(..., description="Shipping carrier name")
    tracking_number: str = Field(..., description="Package tracking number")

    class Config:
        schema_extra = {
            "example": {"carrier": "FedEx", "tracking_number": "FX123456789US"}
        }


class OrderStatusResponse(BaseModel):
    message: str
    order_id: int
    status: str
    tracking_info: Optional[ShippingInfo] = None

    class Config:
        schema_extra = {
            "example": {
                "message": "Order successfully marked as shipped",
                "order_id": 123,
                "status": "shipped",
                "tracking_info": {
                    "carrier": "FedEx",
                    "tracking_number": "FX123456789US",
                },
            }
        }


class LineItemCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="ID of the item to order")
    quantity: int = Field(..., gt=0, description="Quantity of items to order")

    class Config:
        schema_extra = {"example": {"item_id": 1, "quantity": 2}}


class OrderCreate(BaseModel):
    items: List[LineItemCreate] = Field(
        ..., min_items=1, description="Items to include in the order"
    )

    class Config:
        schema_extra = {
            "example": {
                "items": [{"item_id": 1, "quantity": 2}, {"item_id": 3, "quantity": 1}]
            }
        }


class OrderResponse(BaseModel):
    message: str
    order_id: int
    total_price: Decimal
    status: str

    class Config:
        schema_extra = {
            "example": {
                "message": "Order created successfully",
                "order_id": 123,
                "total_price": 59.99,
                "status": "created",
            }
        }


class OrderStatus(enum.Enum):
    CREATED = "created"
    PENDING_PAYMENT = "pending_payment"
    IN_PREPARATION = "in_preparation"
    READY_TO_SHIP = "ready_to_ship"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Order(Base):
    """Customer Orders"""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    tracking_number = Column(String, nullable=True)
    carrier = Column(String, nullable=True)

    # Relationship with LineItem
    line_items = relationship("LineItem", back_populates="order")

    def calculate_total(self, pricing_strategy):
        """Calculates the total price using a pricing strategy"""
        return pricing_strategy.calculate(self)

    def mark_as_paid(self):
        """Mark the order as paid"""
        self.status = OrderStatus.PENDING_PAYMENT

    def mark_as_shipped(self):
        """Mark the order as shipped"""
        self.status = OrderStatus.SHIPPED

    def mark_as_delivered(self):
        """Mark the order as delivered"""
        self.status = OrderStatus.DELIVERED


class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))  # 🔄 antes era item_id
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="line_items")
    product = relationship("Product")  # 🔄 antes era item
