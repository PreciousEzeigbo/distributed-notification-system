"""RabbitMQ queue manager with circuit breaker"""
import pika
import json
import time
from typing import Dict, Any

from .utils.logging_config import setup_logging
from .utils.circuit_breaker import CircuitBreaker

logger = setup_logging("queue-manager")

class QueueManager:
    """Manages RabbitMQ connections and message publishing"""
    
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception
        )
    
    def connect(self, max_retries=5, retry_delay=2):
        """Establish connection to RabbitMQ with retry logic"""
        for attempt in range(max_retries):
            try:
                if self.connection and not self.connection.is_closed:
                    return
                
                parameters = pika.URLParameters(self.rabbitmq_url)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                logger.info("Connected to RabbitMQ")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {str(e)}")
                    raise
    
    def setup_queues(self, exchange_name: str, email_queue: str, push_queue: str, failed_queue: str):
        """Setup exchange and queues"""
        try:
            self.connect()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type='direct',
                durable=True
            )
            
            # Declare email queue
            self.channel.queue_declare(
                queue=email_queue,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': exchange_name,
                    'x-dead-letter-routing-key': 'failed'
                }
            )
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=email_queue,
                routing_key='email'
            )
            
            # Declare push queue
            self.channel.queue_declare(
                queue=push_queue,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': exchange_name,
                    'x-dead-letter-routing-key': 'failed'
                }
            )
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=push_queue,
                routing_key='push'
            )
            
            # Declare failed queue (dead letter queue)
            self.channel.queue_declare(
                queue=failed_queue,
                durable=True
            )
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=failed_queue,
                routing_key='failed'
            )
            
            logger.info(f"Queues setup completed: {email_queue}, {push_queue}, {failed_queue}")
        except Exception as e:
            logger.error(f"Failed to setup queues: {str(e)}")
            raise
    
    def publish_message(
        self,
        exchange: str,
        routing_key: str,
        message: Dict[str, Any],
        correlation_id: str = None
    ):
        """Publish message to queue with circuit breaker"""
        def _publish():
            # Only reconnect if connection is actually closed
            if not self.connection or self.connection.is_closed:
                logger.info("Connection closed, reconnecting...")
                self.connect()
            elif not self.channel or not self.channel.is_open:
                logger.info("Channel closed, reconnecting...")
                self.connect()
            
            properties = pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json',
                correlation_id=correlation_id
            )
            
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=properties
            )
            
            logger.info(f"Message published to {routing_key}: {correlation_id}")
        
        try:
            self.circuit_breaker.call(_publish)
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            raise
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")

# Global queue manager instance
queue_manager = None

def get_queue_manager(rabbitmq_url: str) -> QueueManager:
    """Get or create queue manager instance"""
    global queue_manager
    if queue_manager is None:
        queue_manager = QueueManager(rabbitmq_url)
    return queue_manager
