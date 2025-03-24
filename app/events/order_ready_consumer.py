from app.events.base_consumer import BaseConsumer
from app.config import logger

if __name__ == "__main__":
    try:
        consumer = BaseConsumer(
            queue_name="order_ready_to_ship_queue", routing_key="OrderReadyToShip"
        )
        consumer.start_consuming()
    except KeyboardInterrupt:
        consumer.close()
        logger.info("Consumer for OrderReadyToShip interrupted and closed.")
