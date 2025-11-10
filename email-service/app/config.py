import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin@localhost:5672/")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8002")

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
SMTP_USE_TLS = True

# Queue configuration
EMAIL_QUEUE = "email.queue"
FAILED_QUEUE = "failed.queue"
EXCHANGE_NAME = "notifications.direct"

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
RETRY_MAX_DELAY = 60.0
