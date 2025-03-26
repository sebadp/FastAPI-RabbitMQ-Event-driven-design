from app.events.base_consumer import BaseConsumer, consumer_callback
from app.config import logger

if __name__ == "__main__":
    try:
        consumer = BaseConsumer(
            queue_name="order_created_queue", routing_key="order.created"
        )
        consumer.start_consuming(consumer_callback)

    except KeyboardInterrupt:
        consumer.close()
        logger.info("Consumer for OrderCreated interrupted and closed.")
