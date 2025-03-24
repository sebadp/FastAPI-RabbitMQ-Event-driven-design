# app/models/order_schemas.py
from pydantic import BaseModel, Field, condecimal
from typing import List, Optional
from datetime import datetime
from decimal import Decimal


class ShippingInfo(BaseModel):
    carrier: str = Field(..., description="Name of the shipping carrier")
    tracking_number: str = Field(..., description="Tracking number for the package")

    class Config:
        schema_extra = {
            "example": {"carrier": "FedEx", "tracking_number": "FX123456789US"}
        }


class OrderStatusResponse(BaseModel):
    message: str = Field(..., description="Response message")
    order_id: int = Field(..., description="Unique identifier of the order")
    status: str = Field(..., description="Current status of the order")
    tracking_info: Optional[ShippingInfo] = Field(
        None, description="Shipping information if applicable"
    )

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
    quantity: int = Field(..., gt=0, description="Quantity of the item to order")

    class Config:
        schema_extra = {"example": {"item_id": 1, "quantity": 2}}


class OrderCreate(BaseModel):
    items: List[LineItemCreate] = Field(
        ..., min_items=1, description="List of items for the order"
    )

    class Config:
        schema_extra = {
            "example": {
                "items": [{"item_id": 1, "quantity": 2}, {"item_id": 3, "quantity": 1}]
            }
        }


class OrderResponse(BaseModel):
    message: str = Field(..., description="Response message")
    order_id: int = Field(..., description="Unique identifier of the created order")
    total_price: condecimal(gt=0, decimal_places=2) = Field(
        ..., description="Total price for the order"
    )
    status: str = Field(..., description="Current status of the order")

    class Config:
        schema_extra = {
            "example": {
                "message": "Order created successfully",
                "order_id": 123,
                "total_price": 59.99,
                "status": "created",
            }
        }
