from app.events.base_consumer import BaseConsumer
from app.config import logger

if __name__ == "__main__":
    try:
        consumer = BaseConsumer(
            queue_name="order_created_queue", routing_key="OrderCreated"
        )
        consumer.start_consuming()

    except KeyboardInterrupt:
        consumer.close()
        logger.info("Consumer for OrderCreated interrupted and closed.")
