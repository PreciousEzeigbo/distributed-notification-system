import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://template_service:template_password@localhost:5433/template_service_db"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
