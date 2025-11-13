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
    PUSH_QUEUE, FAILED_QUEUE, EXCHANGE_NAME,
    FCM_CREDENTIALS_FILE,
    MAX_RETRIES, RETRY_BASE_DELAY, RETRY_MAX_DELAY
)
from app.push_sender import PushSender

GATEWAY_URL = os.getenv("GATEWAY_SERVICE_URL", "http://api-gateway:8000")

logger = setup_logging("push-service-worker")

class PushWorker:
    """This worker processes push notifications from the queue."""
    
    def __init__(self):
        self.rabbitmq_url = RABBITMQ_URL
        self.connection = None
        self.channel = None
        self.push_sender = PushSender(credentials_file=FCM_CREDENTIALS_FILE)
        self.retry_handler = RetryHandler(
            max_retries=MAX_RETRIES,
            base_delay=RETRY_BASE_DELAY,
            max_delay=RETRY_MAX_DELAY
        )
    
    def connect(self, max_retries=10, retry_delay=5):
        """Connects to RabbitMQ with retry logic."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                parameters = pika.URLParameters(self.rabbitmq_url)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Sets QoS to process one message at a time
                self.channel.basic_qos(prefetch_count=1)
                
                logger.info(f"Connected to RabbitMQ, listening on {PUSH_QUEUE}")
                return  # Success!
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {str(e)}")
                    raise
                
                wait_time = retry_delay * retry_count
                logger.warning(f"Failed to connect to RabbitMQ (attempt {retry_count}/{max_retries}): {str(e)}")
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

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
                f"{TEMPLATE_SERVICE_URL}/api/v1/templates/render",
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
                f"{GATEWAY_URL}/api/v1/notifications/{notification_type}/status",
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
        """Processes a single push notification message."""
        correlation_id = properties.correlation_id
        set_correlation_id(correlation_id)
        
        try:
            message = json.loads(body)
            logger.info(f"Processing push notification: {message.get('notification_id')}")
            
            notification_id = message.get('notification_id')
            device_token = message.get('recipient')
            template_code = message.get('template_code')
            notification_type = message.get('notification_type', 'push')
            variables = message.get('variables', {})
            priority = message.get('priority', 0)
            metadata = message.get('metadata', {})
            retry_count = message.get('retry_count', 0)
            
            rendered = self.render_template(template_code, variables)
            title = rendered.get('subject', 'Notification')
            body_text = rendered.get('body', '')
            
            image_url = variables.get('meta', {}).get('image_url') if isinstance(variables, dict) else None
            link = variables.get('link') if isinstance(variables, dict) else None
            
            data_payload = {
                'notification_id': str(notification_id),
                'template_code': str(template_code),
                'priority': str(priority)
            }
            if link:
                data_payload['link'] = str(link)
            if metadata:
                # FCM requires all data values to be strings
                data_payload['metadata'] = json.dumps(metadata)
            
            self.push_sender.send_push(
                device_token=device_token,
                title=title,
                body=body_text,
                data=data_payload,
                image_url=image_url
            )
            
            self.update_notification_status(notification_id, notification_type, "delivered")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Push notification sent successfully to {device_token[:20]}...")
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
            message = json.loads(body)
            notification_id = message.get('notification_id')
            notification_type = message.get('notification_type', 'push')
            retry_count = message.get('retry_count', 0)
            
            if retry_count < MAX_RETRIES:
                message['retry_count'] = retry_count + 1
                delay = min(RETRY_BASE_DELAY * (2 ** retry_count), RETRY_MAX_DELAY)
                
                logger.info(f"Requeuing message, retry {retry_count + 1}/{MAX_RETRIES}, delay: {delay}s")
                
                time.sleep(delay)
                
                ch.basic_publish(
                    exchange='',
                    routing_key=PUSH_QUEUE,
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
                queue=PUSH_QUEUE,
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info("Push worker started, waiting for messages...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Push worker stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Error in push worker: {str(e)}")
            raise
    
    def stop(self):
        """Stops the worker and closes RabbitMQ connection."""
        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Push worker stopped")
        except Exception as e:
            logger.error(f"Error stopping worker: {str(e)}")

if __name__ == "__main__":
    worker = PushWorker()
    try:
        worker.start_consuming()
    except Exception as e:
        logger.error(f"Fatal error in standalone push worker: {str(e)}")
        worker.stop()
