from decimal import Decimal
from pydantic import BaseModel, Field


class LineItemDetail(BaseModel):
    item_id: int
    name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class LineItemCreate(BaseModel):
    item_id: int = Field(..., gt=0, description="ID of the item to order")
    quantity: int = Field(..., gt=0, description="Quantity of items to order")

    class Config:
        schema_extra = {"example": {"item_id": 1, "quantity": 2}}
