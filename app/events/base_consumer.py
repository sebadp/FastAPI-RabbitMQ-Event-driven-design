import json
import pika
import time
import os
from app.config import logger
from app.events.dispatcher import dispatch_event
from app.exceptions import EventConsumptionError


class BaseConsumer:
    def __init__(self, queue_name, routing_key, exchange_name="order_exchange"):
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange_name = exchange_name

        # RabbitMQ configuration from environment variables
        rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
        rabbitmq_user = os.environ.get("RABBITMQ_USER", "user")
        rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "password")
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)

        # Attempt to connect to RabbitMQ with retries
        for i in range(5):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=rabbitmq_host, credentials=credentials
                    )
                )
                break
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(
                    f"Attempt {i+1}/5: Unable to connect to RabbitMQ, retrying in 5 seconds..."
                )
                time.sleep(5)
        else:
            raise EventConsumptionError(
                "Could not connect to RabbitMQ after 5 attempts"
            )

        self.channel = self.connection.channel()
        # Declare exchange and queue as durable
        self.channel.exchange_declare(
            exchange=self.exchange_name, exchange_type="direct", durable=True
        )
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_bind(
            exchange=self.exchange_name,
            queue=self.queue_name,
            routing_key=self.routing_key,
        )

    def start_consuming(self, callback):
        """Starts consuming messages using the provided callback."""
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=callback, auto_ack=False
        )
        logger.info(f"Consumer listening on queue: {self.queue_name}")
        self.channel.start_consuming()

    def close(self):
        """Closes the connection to RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Connection to RabbitMQ closed.")


def consumer_callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        logger.info(f"Event received: {event}")
        dispatch_event(event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
