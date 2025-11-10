import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin@localhost:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8002")

# FCM Configuration
FCM_CREDENTIALS_FILE = os.getenv("FCM_CREDENTIALS_FILE", "/app/fcm-credentials.json")

# Queue configuration
PUSH_QUEUE = "push.queue"
FAILED_QUEUE = "failed.queue"
EXCHANGE_NAME = "notifications.direct"

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
RETRY_MAX_DELAY = 60.0
