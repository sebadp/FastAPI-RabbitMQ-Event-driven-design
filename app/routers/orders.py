from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload
from starlette import status

from app.config import logger
from app.events.publisher import EventPublisher
from app.models.database import get_db
from app.models.line_item_model import LineItem
from app.models.order_model import Order
from app.models.order_schemas import OrderResponse, OrderCreate, OrderDetailResponse, OrderStatusResponse
from app.models.product_model import Product
from app.services.pricing import StandardPricing, TaxedPricing

router = APIRouter()
event_publisher = EventPublisher()


@router.post(
    "/orders/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order with multiple items",
    responses={
        400: {"description": "Invalid request data"},
        404: {"description": "One or more items not found"},
        500: {"description": "Server error"},
    },
)
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order with multiple line items.

    ## Request Body
    - `items`: List of items to include in the order, each with an item_id and quantity

    ## Returns
    - `order_id`: ID of the created order
    - `total_price`: Calculated total price (including tax)
    - `status`: Order status

    ## Raises
    - `400 Bad Request`: If the order has no items
    - `404 Not Found`: If any of the requested items don't exist
    """
    if not order_data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must have at least one item.",
        )

    # Create new order
    new_order = Order()
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add line items
    item_ids = [item.item_id for item in order_data.items]
    available_products = {
        p.id: p for p in db.query(Product).filter(Product.id.in_(item_ids)).all()
    }
    missing = [str(id) for id in item_ids if id not in available_products]

    if missing:
        db.rollback()  # Rollback the transaction if items not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Items not found: {', '.join(missing)}",
        )

    # Add line items efficiently
    line_items = []
    for item_data in order_data.items:
        product = available_products[item_data.item_id]
        line_item = LineItem(
            order_id=new_order.id, product_id=product.id, quantity=item_data.quantity
        )
        line_items.append(line_item)
    db.add_all(line_items)
    db.commit()

    # Calculate price using a pricing strategy
    total_price = new_order.calculate_total(TaxedPricing(tax_rate=0.2))

    # Publish event
    event_data = {
        "event": "OrderCreated",
        "order_id": new_order.id,
        "total_price": float(total_price),
    }
    event_publisher.publish_event("order.created", event_data)

    logger.info(f"✅ Order {new_order.id} created with total price: ${total_price:.2f}")

    return OrderResponse(
        message="Order created successfully",
        order_id=new_order.id,
        total_price=total_price,
        status=new_order.status,
    )


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
        .options(joinedload(LineItem.product))
        .all()
    )

    items_detail = [
        {
            "item_id": line.product_id,
            "name": line.product.name,
            "quantity": line.quantity,
            "unit_price": line.product.price,
            "subtotal": line.product.price * line.quantity,
        }
        for line in line_items
    ]
    total_price = order.calculate_total(StandardPricing())
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
    summary="Simulate payment and mark order as paid",
    responses={
        200: {
            "description": "Order status updated to in_preparation and OrderPaid event published"
        },
        400: {"description": "Invalid state for payment"},
        404: {"description": "Order not found"},
    },
)
async def pay_order(
    order_id: int = Path(..., gt=0, description="ID of the order to pay"),
    db: Session = Depends(get_db),
):
    """
    Simulate payment for an order.

    ## Path Parameters
    - **order_id**: Unique identifier of the order to be paid.

    ## Process
    - Validates that the order exists and is in 'pending_payment' status.
    - Updates the order status to 'in_preparation' (simulating successful payment).
    - Publishes the 'OrderPaid' event to trigger subsequent processing.

    ## Returns
    - An OrderStatusResponse containing a success message, the order ID, and the updated status.

    ## Raises
    - 404 Not Found: If the order does not exist.
    - 400 Bad Request: If the order is not in 'pending_payment' state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "pending_payment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be paid in its current state: {order.status}",
        )

    # Simulate payment success and update order status.
    order.status = "in_preparation"
    db.commit()

    event_data = {
        "event": "OrderPaid",
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    event_publisher.publish_event("OrderPaid", event_data)
    logger.info(f"Order {order.id} marked as paid and event published.")

    return OrderStatusResponse(
        message="Order marked as paid", order_id=order.id, status=order.status
    )


@router.post(
    "/orders/{order_id}/ready-to-ship",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark order as ready to ship",
    responses={
        200: {
            "description": "Order status updated to ready_to_ship and OrderReadyToShip event published"
        },
        400: {"description": "Invalid state for marking as ready to ship"},
        404: {"description": "Order not found"},
    },
)
async def mark_order_ready_to_ship(
    order_id: int = Path(
        ..., gt=0, description="ID of the order to mark as ready to ship"
    ),
    db: Session = Depends(get_db),
):
    """
    Mark an order as ready to ship.

    ## Path Parameters
    - **order_id**: Unique identifier of the order to update.

    ## Process
    - Validates that the order exists and is currently in 'in_preparation' state.
    - Updates the order status to 'ready_to_ship'.
    - Publishes the 'OrderReadyToShip' event to notify the carrier for pickup.

    ## Returns
    - An OrderStatusResponse containing a success message, the order ID, and the updated status.

    ## Raises
    - 404 Not Found: If the order does not exist.
    - 400 Bad Request: If the order is not in 'in_preparation' state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "in_preparation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be marked as ready to ship in its current state: {order.status}",
        )

    order.status = "ready_to_ship"
    db.commit()

    event_data = {
        "event": "OrderReadyToShip",
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    event_publisher.publish_event("OrderReadyToShip", event_data)
    logger.info(f"Order {order.id} marked as ready to ship and event published.")

    return OrderStatusResponse(
        message="Order marked as ready to ship", order_id=order.id, status=order.status
    )


@router.post(
    "/orders/{order_id}/shipped",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark order as shipped",
    responses={
        200: {
            "description": "Order status updated to shipped and Shipped event published"
        },
        400: {"description": "Invalid state for shipping"},
        404: {"description": "Order not found"},
    },
)
async def mark_order_shipped(
    order_id: int = Path(..., gt=0, description="ID of the order to mark as shipped"),
    db: Session = Depends(get_db),
):
    """
    Mark an order as shipped.

    ## Path Parameters
    - **order_id**: Unique identifier of the order to be shipped.

    ## Process
    - Validates that the order exists and is in 'ready_to_ship' state.
    - Updates the order status to 'shipped'.
    - Publishes the 'Shipped' event to notify the customer that the package is on the way.

    ## Returns
    - An OrderStatusResponse containing a success message, the order ID, and the updated status.

    ## Raises
    - 404 Not Found: If the order does not exist.
    - 400 Bad Request: If the order is not in 'ready_to_ship' state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "ready_to_ship":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be marked as shipped in its current state: {order.status}",
        )

    order.status = "shipped"
    db.commit()

    event_data = {
        "event": "Shipped",
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    event_publisher.publish_event("Shipped", event_data)
    logger.info(f"Order {order.id} marked as shipped and event published.")

    return OrderStatusResponse(
        message="Order marked as shipped", order_id=order.id, status=order.status
    )


@router.post(
    "/orders/{order_id}/delivered",
    response_model=OrderStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark order as delivered",
    responses={
        200: {
            "description": "Order status updated to delivered and Delivered event published"
        },
        400: {"description": "Invalid state for delivery"},
        404: {"description": "Order not found"},
    },
)
async def mark_order_delivered(
    order_id: int = Path(..., gt=0, description="ID of the order to mark as delivered"),
    db: Session = Depends(get_db),
):
    """
    Mark an order as delivered.

    ## Path Parameters
    - **order_id**: Unique identifier of the order to update.

    ## Process
    - Validates that the order exists and is currently in 'shipped' state.
    - Updates the order status to 'delivered'.
    - Publishes the 'Delivered' event to notify the customer of successful delivery.

    ## Returns
    - An OrderStatusResponse containing a success message, the order ID, and the updated status.

    ## Raises
    - 404 Not Found: If the order does not exist.
    - 400 Bad Request: If the order is not in 'shipped' state.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
        )

    if order.status != "shipped":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be marked as delivered in its current state: {order.status}",
        )

    order.status = "delivered"
    db.commit()

    event_data = {
        "event": "Delivered",
        "order_id": order.id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    event_publisher.publish_event("Delivered", event_data)
    logger.info(f"Order {order.id} marked as delivered and event published.")

    return OrderStatusResponse(
        message="Order marked as delivered", order_id=order.id, status=order.status
    )
