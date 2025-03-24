from app.events.base_consumer import BaseConsumer
from app.config import logger

if __name__ == "__main__":
    try:
        # Consumer para "OrderPaid"
        consumer = BaseConsumer(queue_name="order_paid_queue", routing_key="OrderPaid")
        consumer.start_consuming()
    except KeyboardInterrupt:
        consumer.close()
        logger.info("Consumer for OrderPaid interrupted and closed.")
