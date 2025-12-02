import json
import pika
from app.config import settings
from app.mailer import notify


class RabbitMQSubscriber:
    def __init__(self, logger, queue_name=None):
        self.logger = logger
        self.queue_name = queue_name if queue_name else settings.QUEUE_TO_SUBSCRIBE
        self.connection = None
        self.channel = None

    def connect(self):
        try:
            if not self.connection or self.connection.is_closed:
                self.logger.info(f"connecting to rabbitmq at {settings.RABBITMQ_HOST}")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=settings.RABBITMQ_HOST)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name)
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.callback
                )
                self.logger.info(f"subscribed to queue {self.queue_name}")
        except Exception:
            self.logger.error("connection error", exc_info=True)
            raise

    def close(self):
        try:
            if self.connection and self.connection.is_open:
                self.logger.info("closing queue connection")
                self.connection.close()
        except Exception:
            self.logger.error("error closing connection", exc_info=True)

    def callback(self, ch, method, properties, body):
        try:
            payload = json.loads(body)
        except Exception:
            self.logger.error("invalid json", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag)
            return
        try:
            err = notify(payload)
        except Exception:
            self.logger.error("handler failure", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag)
            return
        if err:
            self.logger.warning("handler returned error")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.info(f"message processed from {self.queue_name}")

    def start_consuming(self):
        try:
            self.connect()
            self.logger.info(f"started consuming from {self.queue_name}")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            try:
                self.channel.stop_consuming()
            except Exception:
                self.logger.error("stop consuming error", exc_info=True)
        except Exception:
            self.logger.error("consumer loop error", exc_info=True)
        finally:
            self.close()
