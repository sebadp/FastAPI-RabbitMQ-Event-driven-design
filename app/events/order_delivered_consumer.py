from app.events.base_consumer import BaseConsumer, consumer_callback
from app.config import logger

if __name__ == "__main__":
    try:
        consumer = BaseConsumer(
            queue_name="order_delivered_queue", routing_key="order.delivered"
        )
        consumer.start_consuming(consumer_callback)
    except KeyboardInterrupt:
        consumer.close()
        logger.info("Consumer for OrderDelivered interrupted and closed.")
