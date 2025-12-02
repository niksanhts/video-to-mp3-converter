import json
import pika
from pika.exceptions import AMQPError
from app import logger
from app.config import settings


class RabbitMQPublisher:
    def __init__(self, queue_name=None):
        self.queue_name = queue_name if queue_name else settings.QUEUE_TO_PUBLISH
        self._conn = None
        self._channel = None

    def connect(self):
        try:
            if not self._conn or self._conn.is_closed:
                logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST} for publishing")
                self._conn = pika.BlockingConnection(
                    pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
                )
                self._channel = self._conn.channel()
                self._channel.queue_declare(queue=self.queue_name)
                logger.info(f"Successfully connected and declared queue: {self.queue_name}")
        except AMQPError:
            logger.error("AMQP error occurred during publisher connection", exc_info=True)
            raise
        except Exception:
            logger.error("Unexpected error during publisher connection", exc_info=True)
            raise

    def close(self):
        try:
            if self._conn and self._conn.is_open:
                logger.info("Closing RabbitMQ publisher connection")
                self._conn.close()
                logger.info("RabbitMQ publisher connection closed")
        except Exception:
            logger.error("Error occurred while closing RabbitMQ publisher connection", exc_info=True)

    def publish(self, message):
        self.connect()
        try:
            logger.info(f"Publishing message to {self.queue_name}: {message}")
            self._channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            logger.info(f"Message successfully sent to {self.queue_name}")
        except AMQPError:
            logger.error("AMQP error occurred during message publish", exc_info=True)
            raise
        except Exception:
            logger.error("Unexpected error during message publish", exc_info=True)
            raise
        finally:
            self.close()


rabbitmq_publisher = RabbitMQPublisher()
