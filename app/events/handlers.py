from app.models.database import SessionLocal
from app.models.order_model import Order
from app.events.publisher import EventPublisher
from app.config import logger

event_publisher = EventPublisher()


def handle_order_created(event: dict):
    """When an order is created: update it to 'pending_payment' and notify the user."""
    order_id = event.get("order_id")
    total_price = event.get("total_price")
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "pending_payment"
        db.commit()
        logger.info(f"Order {order_id} updated to pending_payment")
        # Simulate user notification
        logger.info(
            f"User notification: Please pay for order {order_id} with total amount ${total_price}"
        )
    db.close()


def handle_order_payed(event: dict):
    """Simulate payment: update to 'in_preparation' and notify the supplier to prepare the package."""
    order_id = event.get("order_id")
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "in_preparation"  # updated status for consistency
        db.commit()
        logger.info(f"Order {order_id} updated to in_preparation")
        # Simulate notification to supplier
        logger.info(f"Message to supplier: Prepare the package for order {order_id}")
    db.close()


def handle_order_ready_to_ship(event: dict):
    """Triggered from an endpoint (not implemented here), this event notifies the carrier and updates to 'ready_to_ship'."""
    order_id = event.get("order_id")
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "ready_to_ship"
        db.commit()
        logger.info(f"Order {order_id} updated to ready_to_ship")
        # Simulate sending message to the carrier
        logger.info(f"Message to carrier: Pick up the package for order {order_id}")
    db.close()


def handle_shipped(event: dict):
    """When the carrier notifies that the package has been picked up, publish 'Shipped' to notify the user."""
    order_id = event.get("order_id")
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "shipped"
        db.commit()
        logger.info(f"Order {order_id} updated to shipped")
        # Notify the user
        logger.info(f"User notification: Your order {order_id} is on its way.")
    db.close()


def handle_delivered(event: dict):
    """When the carrier marks the order as delivered, update the status to 'delivered' and notify the user."""
    order_id = event.get("order_id")
    db = SessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        order.status = "delivered"
        db.commit()
        logger.info(f"Order {order_id} updated to delivered")
        # Notify the user
        logger.info(f"User notification: Your order {order_id} has been delivered.")
    db.close()
