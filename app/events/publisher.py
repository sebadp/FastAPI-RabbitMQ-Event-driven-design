from datetime import datetime

import pika
import json
import time
from app.config import logger
from app.exceptions import EventPublishingError
import json
from decimal import Decimal


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class EventPublisher:
    def __init__(self, exchange_name="order_exchange"):
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None

    def _connect(self):
        """Establishes a connection to RabbitMQ if not already connected"""
        if self.connection is None or self.connection.is_closed:
            rabbitmq_host = "rabbitmq"
            rabbitmq_user = "user"
            rabbitmq_pass = "password"

            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

            # Retry loop in case RabbitMQ is not ready yet
            for i in range(5):
                try:
                    self.connection = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host=rabbitmq_host, credentials=credentials
                        )
                    )
                    self.channel = self.connection.channel()
                    self.channel.exchange_declare(
                        exchange=self.exchange_name, exchange_type="direct"
                    )
                    logger.info("✅ Connected to RabbitMQ")
                    break
                except pika.exceptions.AMQPConnectionError as e:
                    logger.warning(
                        f"⚠️ Attempt {i+1}/5: Could not connect to RabbitMQ, retrying in 5 seconds..."
                    )
                    time.sleep(5)
            else:
                raise Exception("❌ Failed to connect to RabbitMQ after 5 attempts.")

    def publish_event(self, event_type, data):
        """Publishes an event to RabbitMQ with error handling"""
        self._connect()  # Ensure connection is established before publishing
        try:
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=event_type,
                body=json.dumps(data, cls=EnhancedJSONEncoder),
                properties=pika.BasicProperties(
                    delivery_mode=2  # Ensures message persistence
                ),
            )
            logger.info(f"📡 Event published: {event_type} - {data}")
        except Exception as e:
            error_message = EventPublishingError(event_type, e)
            logger.error(f"❌ {error_message}")
            raise error_message

    def close(self):
        """Closes RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
