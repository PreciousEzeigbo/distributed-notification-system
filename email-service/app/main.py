import pika
import json
import time
import requests
import os
import sys

# Add parent directory to path so we can import from app.utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logging_config import setup_logging, set_correlation_id
from app.utils.retry_handler import RetryHandler

from app.config import (
    RABBITMQ_URL, REDIS_URL, TEMPLATE_SERVICE_URL,
    EMAIL_QUEUE, FAILED_QUEUE, EXCHANGE_NAME,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_USE_TLS,
    MAX_RETRIES, RETRY_BASE_DELAY, RETRY_MAX_DELAY
)
from app.email_sender import EmailSender

GATEWAY_URL = os.getenv("GATEWAY_SERVICE_URL", "http://api-gateway:8000")

logger = setup_logging("email-service-worker")

class EmailWorker:
    """This worker processes email notifications from the queue."""
    
    def __init__(self):
        self.rabbitmq_url = RABBITMQ_URL
        self.connection = None
        self.channel = None
        self.email_sender = EmailSender(
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
            smtp_user=SMTP_USER,
            smtp_password=SMTP_PASSWORD,
            smtp_from=SMTP_FROM_EMAIL,
            use_tls=SMTP_USE_TLS
        )
        self.retry_handler = RetryHandler(
            max_retries=MAX_RETRIES,
            base_delay=RETRY_BASE_DELAY,
            max_delay=RETRY_MAX_DELAY
        )
    
    def connect(self):
        """Connects to RabbitMQ."""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.basic_qos(prefetch_count=1)
            
            logger.info(f"Connected to RabbitMQ, listening on {EMAIL_QUEUE}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    def check_connection(self) -> bool:
        """Checks RabbitMQ connection without starting consumption."""
        try:
            self.connect()
            self.stop()
            return True
        except Exception:
            return False
    
    def render_template(self, template_name: str, variables: dict, language: str = "en") -> dict:
        """Fetches and renders a template from the template service."""
        try:
            response = requests.post(
                f"{TEMPLATE_SERVICE_URL}/templates/render",
                json={
                    "template_name": template_name,
                    "language": language,
                    "variables": variables
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            raise
    
    def update_notification_status(self, notification_id: int, notification_type: str, status: str, error_message: str = None):
        """Updates notification status in the API Gateway."""
        try:
            from datetime import datetime
            
            response = requests.post(
                f"{GATEWAY_URL}/notifications/{notification_type}/status",
                json={
                    "notification_id": str(notification_id),
                    "status": status,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": error_message
                },
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Notification {notification_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")
    
    def process_message(self, ch, method, properties, body):
        """Processes a single email message."""
        correlation_id = properties.correlation_id
        set_correlation_id(correlation_id)
        
        try:
            message = json.loads(body)
            logger.info(f"Processing email notification: {message.get('notification_id')}")
            
            notification_id = message.get('notification_id')
            recipient = message.get('recipient')
            template_code = message.get('template_code')
            notification_type = message.get('notification_type', 'email')
            variables = message.get('variables', {})
            priority = message.get('priority', 0)
            metadata = message.get('metadata', {})
            retry_count = message.get('retry_count', 0)
            
            # Render the template
            rendered = self.render_template(template_code, variables)
            subject = rendered.get('subject', 'Notification')
            body = rendered.get('body', '')
            
            # Send email
            self.email_sender.send_email(
                to_email=recipient,
                subject=subject,
                body=body,
                is_html=True
            )
            
            self.update_notification_status(notification_id, notification_type, "delivered")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Email sent successfully to {recipient}")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            # Checks retry count
            message = json.loads(body)
            notification_id = message.get('notification_id')
            notification_type = message.get('notification_type', 'email')
            retry_count = message.get('retry_count', 0)
            
            if retry_count < MAX_RETRIES:
                message['retry_count'] = retry_count + 1
                delay = min(RETRY_BASE_DELAY * (2 ** retry_count), RETRY_MAX_DELAY)
                
                logger.info(f"Requeuing message, retry {retry_count + 1}/{MAX_RETRIES}, delay: {delay}s")
                
                time.sleep(delay)
                
                ch.basic_publish(
                    exchange='',
                    routing_key=EMAIL_QUEUE,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        correlation_id=correlation_id
                    )
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error(f"Max retries reached, sending to failed queue")
                self.update_notification_status(notification_id, notification_type, "failed", str(e))
                
                ch.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key='failed',
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        correlation_id=correlation_id
                    )
                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def start_consuming(self):
        """Starts consuming messages from the queue."""
        try:
            self.connect()
            self.channel.basic_consume(
                queue=EMAIL_QUEUE,
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info("Email worker started, waiting for messages...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Email worker stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in email worker: {str(e)}")
            raise
    
    def stop(self):
        """Stops the worker and closes RabbitMQ connection."""
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Email worker stopped")
        except Exception as e:
            logger.error(f"Error stopping worker: {str(e)}")

# FastAPI app for health checks (optional - only needed if running with uvicorn)
# Commenting out to run as pure worker without FastAPI dependency
# app = FastAPI(
#     title="Email Service Worker",
#     description="Consumes messages from the email queue and sends emails",
#     version="1.0.0"
# )

# @app.on_event("startup")
# async def startup_event():
#     """Initializes the worker and connects to RabbitMQ on startup."""
#     global email_worker
#     email_worker = EmailWorker()
#     # For simplicity, we'll just connect here and assume a separate consumer process
#     # will be managed by the deployment environment
#     try:
#         email_worker.connect()
#         logger.info("Email service connected to RabbitMQ. Consumer should be started separately.")
#     except Exception as e:
#         logger.error(f"Failed to connect to RabbitMQ on startup: {e}")

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Closes RabbitMQ connection on shutdown."""
#     global email_worker
#     if email_worker:
#         email_worker.stop()

# @app.get("/health", status_code=status.HTTP_200_OK)
# async def health_check(response: Response):
#     """
#     Health check endpoint.
#     Checks RabbitMQ connection.
#     """
#     try:
#         # Attempts to connect to RabbitMQ to verify its health
#         worker_test = EmailWorker()
#         worker_test.connect()
#         worker_test.stop() # Closes connection immediately after check
#         return {"status": "healthy", "message": "Email service is operational and connected to RabbitMQ."}
#     except Exception as e:
#         logger.error(f"Health check failed: {e}")
#         response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
#         return {"status": "unhealthy", "message": f"Email service is not connected to RabbitMQ: {e}"}

if __name__ == "__main__":
    # This block runs if main.py is executed directly, not via uvicorn.
    # When running with uvicorn, the startup_event handles the connection.
    # For local testing or as a standalone worker, this can be used.
    worker = EmailWorker()
    try:
        worker.start_consuming()
    except Exception as e:
        logger.error(f"Fatal error in standalone email worker: {str(e)}")
        worker.stop()
