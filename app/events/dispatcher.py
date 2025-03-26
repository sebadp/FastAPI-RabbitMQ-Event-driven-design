from app.config import logger

from app.events.handlers import (
    handle_order_created,
    handle_order_payed,
    handle_order_ready_to_ship,
    handle_shipped,
    handle_delivered,
)

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


register_handler("order.created", handle_order_created)
register_handler("order.paid", handle_order_payed)
register_handler("order.ready.to.ship", handle_order_ready_to_ship)
register_handler("order.shipped", handle_shipped)
register_handler("order.delivered", handle_delivered)
