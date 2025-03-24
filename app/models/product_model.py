from typing import List, Optional

from pydantic import BaseModel, validator, Field, condecimal
from sqlalchemy import Column, Integer, String, Float, Numeric, DateTime
from datetime import datetime
from app.models.database import Base


class Product(Base):
    """Product model"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)


# Product Schema with improved validation and documentation
class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        example="Ergonomic Keyboard",
        description="Product name (1-100 characters)",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        example="Mechanical keyboard with ergonomic design",
        description="Optional product description (max 500 characters)",
    )
    price: condecimal(gt=0, decimal_places=2) = Field(
        ..., example=99.99, description="Product price (greater than 0)"
    )
    stock: int = Field(
        ..., ge=0, example=25, description="Available inventory quantity (0 or greater)"
    )

    @validator("name")
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or just whitespace")
        return v.strip()

    class Config:
        schema_extra = {
            "example": {
                "name": "Gaming Mouse",
                "description": "High-precision gaming mouse with adjustable DPI",
                "price": 49.99,
                "stock": 100,
            }
        }


class ProductResponse(ProductCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Gaming Mouse",
                "description": "High-precision gaming mouse with adjustable DPI",
                "price": 49.99,
                "stock": 100,
                "created_at": "2025-03-20T18:30:45.123Z",
                "updated_at": None,
            }
        }


class ProductList(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name": "Gaming Mouse",
                        "description": "High-precision gaming mouse with adjustable DPI",
                        "price": 49.99,
                        "stock": 100,
                        "created_at": "2025-03-20T18:30:45.123Z",
                        "updated_at": None,
                    }
                ],
                "total": 42,
                "page": 1,
                "page_size": 20,
                "pages": 3,
            }
        }
