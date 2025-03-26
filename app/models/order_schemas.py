from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.line_item_schemas import LineItemDetail, LineItemCreate


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
