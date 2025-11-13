from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from . import models, config
from .database import engine
from .routes import router as notification_router
from .queue_manager import get_queue_manager
from .cache_manager import get_cache_manager
from .utils.logging_config import setup_logging, set_correlation_id
from .utils.response_models import APIResponse

logger = setup_logging("api-gateway")

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Gateway",
    description="Entry point for all notification requests with routing and status tracking",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc),
            "data": None,
            "meta": None
        }
    )

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize queue manager and setup queues"""
    try:
        logger.info("Starting API Gateway...")
        
        # Setup RabbitMQ queues
        queue_mgr = get_queue_manager(config.RABBITMQ_URL)
        queue_mgr.setup_queues(
            exchange_name=config.EXCHANGE_NAME,
            email_queue=config.EMAIL_QUEUE,
            push_queue=config.PUSH_QUEUE,
            failed_queue=config.FAILED_QUEUE
        )
        
        # Test Redis connection
        cache_mgr = get_cache_manager(config.REDIS_URL)
        cache_mgr.connect()
        
        logger.info("API Gateway startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down API Gateway...")
        queue_mgr = get_queue_manager(config.RABBITMQ_URL)
        queue_mgr.close()
        logger.info("API Gateway shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

app.include_router(notification_router, prefix="/api/v1/notifications", tags=["notifications"])

# Include user and template proxy routes under /api/v1
from .routes import router as notification_router, user_router, template_router
app.include_router(user_router, prefix="/api/v1", tags=["users"])
app.include_router(template_router, prefix="/api/v1", tags=["templates"])

@app.get("/")
def read_root():
    return APIResponse(
        message="API Gateway is running",
        data={"service": "api-gateway", "version": "1.0.0", "endpoints": "/api/v1/notifications"}
    )

@app.get("/api/v1/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        from .database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        db.close()
        
        if result != 1:
            raise Exception("Database query returned unexpected result")
        
        # Test RabbitMQ connection
        queue_mgr = get_queue_manager(config.RABBITMQ_URL)
        queue_mgr.connect()
        
        # Test Redis connection
        cache_mgr = get_cache_manager(config.REDIS_URL)
        cache_mgr.connect()
        
        return APIResponse(
            message="API Gateway is healthy",
            data={
                "status": "healthy",
                "service": "api-gateway",
                "version": "1.0.0",
                "checks": {
                    "database": "ok",
                    "rabbitmq": "ok",
                    "redis": "ok"
                }
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Service unhealthy",
                "error": str(e),
                "data": {
                    "status": "unhealthy",
                    "service": "api-gateway",
                    "version": "1.0.0"
                },
                "meta": None
            }
        )