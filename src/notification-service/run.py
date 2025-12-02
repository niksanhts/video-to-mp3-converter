from app import logger 
from app.config import settings
from app.subscriber import RabbitMQSubscriber

logger.info(f"Starting {settings.PROJECT_NAME}")

try:
    rabbitmq_subscriber = RabbitMQSubscriber(logger=logger)
    rabbitmq_subscriber.start_consuming()
except Exception as e:
    logger.error("Unhandled exception occurred during consumer execution", exc_info=True)
    try:
        rabbitmq_subscriber.stop()
    except Exception:
        logger.error("Failed to stop RabbitMQ subscriber cleanly", exc_info=True)
