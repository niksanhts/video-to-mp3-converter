import pika
from pika.exceptions import AMQPError
from app import logger
from app.config import settings
from app.converter import convert


class RabbitMQSubscriber:
    def __init__(self, queue_name=None):
        self.queue_name = queue_name if queue_name else settings.QUEUE_TO_SUBSCRIBE
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            if not self.connection or self.connection.is_closed:
                logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name)
                self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
                logger.info(f"Successfully connected and subscribed to queue: {self.queue_name}")
        except AMQPError:
            logger.error("AMQP error occurred while connecting to RabbitMQ", exc_info=True)
            raise
        except Exception:
            logger.error("Unexpected error during RabbitMQ connection", exc_info=True)
            raise

    def close(self):
        try:
            if self.connection and self.connection.is_open:
                logger.info("Closing RabbitMQ connection")
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception:
            logger.error("Error occurred while closing RabbitMQ connection", exc_info=True)

    def callback(self, ch, method, properties, body):
        try:
            logger.info(f"Received message from queue {self.queue_name}")
            err = convert(body)
            if err:
                logger.warning(f"Message processing failed for: {body}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Message successfully processed from {self.queue_name}: {body}")
        except Exception:
            logger.error(f"Unexpected error in callback for message: {body}", exc_info=True)
            try:
                ch.basic_nack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.error("Failed to NACK message after callback exception", exc_info=True)

    def start_consuming(self):
        try:
            self.connect()
            logger.info(f"Started consuming from queue: {self.queue_name}")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt received, stopping consumption")
            try:
                self.channel.stop_consuming()
            except Exception:
                logger.error("Error stopping channel consumption", exc_info=True)
        except AMQPError:
            logger.error("AMQP error occurred during consumption", exc_info=True)
        except Exception:
            logger.error("Unexpected error during consumption", exc_info=True)
        finally:
            self.close()


rabbitmq_subscriber = RabbitMQSubscriber()
