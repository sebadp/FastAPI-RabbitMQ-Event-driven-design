import pika
import os

rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "user")
rabbitmq_pass = os.environ.get("RABBITMQ_PASS", "password")

credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
connection_params = pika.ConnectionParameters(
    host=rabbitmq_host, credentials=credentials
)

try:
    connection = pika.BlockingConnection(connection_params)
    print("✅ Conexión exitosa a RabbitMQ!")
    connection.close()
except Exception as e:
    print("❌ Error al conectar:", e)
