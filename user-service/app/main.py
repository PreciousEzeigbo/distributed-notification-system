from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from . import models
from .database import engine
from .routes import router as user_router
from .utils.logging_config import setup_logging, set_correlation_id
from .utils.response_models import APIResponse

logger = setup_logging("user-service")

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Service",
    description="Manages user information, authentication, and notification preferences",
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

app.include_router(user_router, prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    """Root endpoint"""
    return APIResponse(
        message="User Service is running", 
        data={
            "service": "user-service", 
            "version": "1.0.0",
            "status": "operational"
        }
    )

@app.get("/health")
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
        
        return APIResponse(
            message="User Service is healthy",
            data={
                "status": "healthy",
                "service": "user-service",
                "version": "1.0.0",
                "database": "connected",
                "checks": {
                    "database": "ok"
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
                    "service": "user-service",
                    "version": "1.0.0",
                    "checks": {
                        "database": "failed"
                    }
                },
                "meta": None
            }
        )