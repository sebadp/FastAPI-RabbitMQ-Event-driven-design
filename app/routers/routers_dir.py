# orders.py

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session, joinedload
from starlette import status

from app.events.publisher import EventPublisher
from app.config import logger
from app.models.database import get_db
from app.models.order_model import (
    Order,
    LineItem,
    Item,
    OrderResponse,
    OrderCreate,
    OrderStatusResponse,
    ShippingInfo,
    OrderDetailResponse,
)
from app.services.pricing import StandardPricing, TaxedPricing

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.events.publisher import EventPublisher
from app.config import logger
from app.models.database import get_db
from app.models.order_model import Order

router = APIRouter()
event_publisher = EventPublisher()


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get order details by ID",
    responses={
        200: {"description": "Order details retrieved successfully"},
        404: {"description": "Order not found"},
    },
)
async def get_order(
    order_id: int = Path(..., gt=0, description="The ID of the order to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Retrieve detailed information about a specific order.

    ## Path Parameter
    - `order_id`: The unique identifier of the order

    ## Returns
    - Full order details including ID, status, line items, and calculated total price

    ## Raises
    - `404 Not Found`: If the order with the specified ID doesn't exist
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    # Eagerly load line items with their related items to reduce database queries
    line_items = (
        db.query(LineItem)
        .filter(LineItem.order_id == order_id)
        .options(joinedload(LineItem.item))
        .all()
    )

    total_price = order.calculate_total(TaxedPricing(tax_rate=0.2))

    # Build response with line item details
    items_detail = [
        {
            "item_id": line.item_id,
            "name": line.item.name,
            "quantity": line.quantity,
            "unit_price": line.item.price,
            "subtotal": line.item.price * line.quantity,
        }
        for line in line_items
    ]

    return OrderDetailResponse(
        order_id=order.id,
        status=order.status,
        created_at=order.created_at,
        items=items_detail,
        total_price=total_price,
    )


@router.post(
    "/orders/{order_id}/pay",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an order as paid",
    responses={
        200: {"description": "Order successfully marked as paid"},
        400: {"description": "Order cannot be paid in its current state"},
        404: {"description": "Order not found"},
    },
)
async def pay_order(
    order_id: int = Path(..., gt=0, description="The ID of the order to mark as paid"),
    db: Session = Depends(get_db),
):
    """
    Mark an existing order as paid and publish an OrderPaid event.

    ## Path Parameter
    - `order_id`: The unique identifier of the order to pay

    ## Returns
    - Confirmation message and updated order status

    ## Raises
    - `404 Not Found`: If the order with the specified ID doesn't exist
    - `400 Bad Request`: If the order is not in a state where it can be paid
      (e.g., already paid or shipped)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "created":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be paid in its current state: {order.status}",
        )

    order.mark_as_paid()
    db.commit()

    event_data = {
        "event": "OrderPaid",
        "order_id": order.id,
        "paid_at": datetime.now().isoformat(),
    }
    event_publisher.publish_event("order.paid", event_data)

    logger.info(f"✅ Order {order.id} marked as PAID")

    return OrderStatusResponse(
        message="Order successfully marked as paid",
        order_id=order.id,
        status=order.status,
    )


@router.post(
    "/orders/{order_id}/ship",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark an order as shipped",
    responses={
        200: {"description": "Order successfully marked as shipped"},
        400: {"description": "Order cannot be shipped in its current state"},
        404: {"description": "Order not found"},
    },
)
async def ship_order(
    order_id: int = Path(
        ..., gt=0, description="The ID of the order to mark as shipped"
    ),
    shipping_info: Optional[ShippingInfo] = Body(
        None, description="Optional shipping information"
    ),
    db: Session = Depends(get_db),
):
    """
    Mark an existing order as shipped and publish an OrderShipped event.

    ## Path Parameter
    - `order_id`: The unique identifier of the order to ship

    ## Request Body (Optional)
    - `shipping_info`: Optional shipping details such as tracking number and carrier

    ## Returns
    - Confirmation message and updated order status

    ## Raises
    - `404 Not Found`: If the order with the specified ID doesn't exist
    - `400 Bad Request`: If the order is not in a state where it can be shipped
      (e.g., not yet paid or already shipped)
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order must be paid before shipping. Current status: {order.status}",
        )

    order.mark_as_shipped()

    # If shipping info is provided, store it with the order
    if shipping_info:
        order.tracking_number = shipping_info.tracking_number
        order.carrier = shipping_info.carrier

    db.commit()

    event_data = {
        "event": "OrderShipped",
        "order_id": order.id,
        "shipped_at": datetime.now().isoformat(),
        "tracking_info": shipping_info.dict() if shipping_info else None,
    }
    event_publisher.publish_event("order.shipped", event_data)

    logger.info(f"📦 Order {order.id} marked as SHIPPED")

    return OrderStatusResponse(
        message="Order successfully marked as shipped",
        order_id=order.id,
        status=order.status,
        tracking_info=shipping_info,
    )


# products.py

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.models.database import get_db
from app.models.order_model import LineItem
from app.models.product_model import (
    Product,
    ProductList,
    ProductResponse,
    ProductCreate,
)
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


# List all products with pagination
@router.get(
    "/products/",
    response_model=ProductList,
    summary="List all products with pagination",
    responses={
        200: {"description": "List of products successfully retrieved"},
        400: {"description": "Invalid query parameters"},
    },
)
async def list_products(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    page_size: int = Query(
        20, ge=1, le=100, description="Number of items per page (1-100)"
    ),
    sort_by: str = Query("id", description="Field to sort by (id, name, price, stock)"),
    sort_order: str = Query("asc", description="Sort order (asc, desc)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    search: Optional[str] = Query(
        None, min_length=2, description="Search in name and description"
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve a paginated list of products with sorting and filtering options.

    ## Query Parameters
    - `page`: Page number (starts at 1)
    - `page_size`: Number of items per page (1-100)
    - `sort_by`: Field to sort by (id, name, price, stock)
    - `sort_order`: Sort direction (asc, desc)
    - `min_price`: Filter by minimum price
    - `max_price`: Filter by maximum price
    - `in_stock`: Filter by stock availability
    - `search`: Search term for name and description

    ## Returns
    A paginated list of products with total count information
    """
    # Start with base query
    query = db.query(Product)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) | (Product.description.ilike(search_term))
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if in_stock is not None:
        if in_stock:
            query = query.filter(Product.stock > 0)
        else:
            query = query.filter(Product.stock == 0)

    # Get total count before pagination
    total_items = query.count()

    # Apply sorting
    valid_sort_fields = {"id", "name", "price", "stock", "created_at"}
    if sort_by not in valid_sort_fields:
        sort_by = "id"

    sort_column = getattr(Product, sort_by)
    if sort_order.lower() == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    query = query.order_by(sort_column)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Get results
    products = query.all()

    # Calculate total pages
    total_pages = (total_items + page_size - 1) // page_size

    return {
        "items": products,
        "total": total_items,
        "page": page,
        "page_size": page_size,
        "pages": total_pages,
    }


# Get product details
@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get detailed product information",
    responses={
        200: {"description": "Product details successfully retrieved"},
        404: {"description": "Product not found"},
    },
)
async def get_product(
    product_id: int = Path(..., gt=0, description="The ID of the product to retrieve"),
    db: Session = Depends(get_db),
):
    """
    Retrieve detailed information about a specific product.

    ## Path Parameter
    - **product_id**: The unique identifier of the product

    ## Returns
    Detailed product information including stock level and pricing

    ## Raises
    - **404 Not Found**: If the product with the specified ID doesn't exist
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return product


# Add a new product
@router.post(
    "/products/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    responses={
        201: {"description": "Product successfully created"},
        400: {"description": "Invalid product data"},
        409: {"description": "Product with this name already exists"},
    },
)
async def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product in the inventory.

    ## Request Body
    - `name`: Product name (required)
    - `description`: Optional product description
    - `price`: Product price (required, > 0)
    - `stock`: Available inventory (required, >= 0)

    ## Returns
    The created product with its assigned ID

    ## Raises
    - `400 Bad Request`: If the product data is invalid
    - `409 Conflict`: If a product with the same name already exists
    """
    try:
        # Check if product name already exists
        existing_product = (
            db.query(Product).filter(Product.name == product.name).first()
        )
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with name '{product.name}' already exists",
            )

        new_product = Product(
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            created_at=datetime.utcnow(),
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create product due to database constraint violation",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


# Update product information
@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Update an existing product",
    responses={
        200: {"description": "Product successfully updated"},
        400: {"description": "Invalid product data"},
        404: {"description": "Product not found"},
        409: {"description": "Name conflict with existing product"},
    },
)
async def update_product(
    product_id: int = Path(..., gt=0, description="The ID of the product to update"),
    product_data: ProductCreate = Body(...),
    db: Session = Depends(get_db),
):
    """
    Update an existing product's information.

    ## Path Parameter
    - `product_id`: The unique identifier of the product to update

    ## Request Body
    - `name`: Updated product name
    - `description`: Updated product description
    - `price`: Updated product price
    - `stock`: Updated inventory level

    ## Returns
    The updated product information

    ## Raises
    - `404 Not Found`: If the product doesn't exist
    - `409 Conflict`: If updating would create a name conflict
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        # Check for name conflict if name is being changed
        if product_data.name != product.name:
            existing = (
                db.query(Product).filter(Product.name == product_data.name).first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with name '{product_data.name}' already exists",
                )

        # Update fields
        for key, value in product_data.dict().items():
            setattr(product, key, value)

        # Update the updated_at timestamp
        product.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not update product due to database constraint violation",
        )


# Delete a product
@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    responses={
        204: {"description": "Product successfully deleted"},
        404: {"description": "Product not found"},
        400: {"description": "Cannot delete product with active orders"},
    },
)
async def delete_product(
    product_id: int = Path(..., gt=0, description="The ID of the product to delete"),
    db: Session = Depends(get_db),
):
    """
    Delete a product from the inventory.

    ## Path Parameter
    - `product_id`: The unique identifier of the product to delete

    ## Returns
    No content on successful deletion

    ## Raises
    - `404 Not Found`: If the product doesn't exist
    - `400 Bad Request`: If the product cannot be deleted (e.g., referenced by orders)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    # Check if product is used in any line items (you may need to adjust this query)
    if (
        hasattr(Product, "line_items")
        and db.query(LineItem).filter(LineItem.item_id == product_id).count() > 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete product that is referenced in existing orders",
        )

    try:
        db.delete(product)
        db.commit()
        return None  # 204 No Content
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting: {str(e)}",
        )
