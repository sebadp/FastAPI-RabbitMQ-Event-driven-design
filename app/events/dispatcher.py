from app.config import logger

handlers = {}


def register_handler(event_type: str, handler_func):
    handlers[event_type] = handler_func
    logger.info(f"Registered handler for event: {event_type}")


def dispatch_event(event: dict):
    event_type = event.get("event")
    if event_type in handlers:
        logger.info(f"Dispatching event: {event_type}")
        return handlers[event_type](event)
    else:
        logger.warning(f"No handler registered for event: {event_type}")


from app.events.handlers import (
    handle_order_created,
    handle_order_payed,
    handle_order_ready_to_ship,
    handle_shipped,
    handle_delivered,
)

register_handler("OrderCreated", handle_order_created)
register_handler("OrderPaid", handle_order_payed)
register_handler("OrderReadyToShip", handle_order_ready_to_ship)
register_handler("Shipped", handle_shipped)
register_handler("Delivered", handle_delivered)
