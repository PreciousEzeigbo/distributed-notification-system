import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gateway_service:gateway_password@localhost:5434/gateway_service_db"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:admin@localhost:5672/")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
TEMPLATE_SERVICE_URL = os.getenv("TEMPLATE_SERVICE_URL", "http://localhost:8002")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"

# Queue configuration
EMAIL_QUEUE = "email.queue"
PUSH_QUEUE = "push.queue"
FAILED_QUEUE = "failed.queue"
EXCHANGE_NAME = "notifications.direct"
