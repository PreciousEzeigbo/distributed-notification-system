from fastapi import APIRouter, Depends, HTTPException, status, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any
import uuid
from uuid import UUID
from datetime import datetime
from . import models, schemas, config
from .database import get_db
from .queue_manager import get_queue_manager
from .cache_manager import get_cache_manager
from .utils.logging_config import setup_logging, get_correlation_id
import requests

logger = setup_logging("api-gateway")

router = APIRouter()
user_router = APIRouter()
template_router = APIRouter()

# Initialize managers
queue_mgr = get_queue_manager(config.RABBITMQ_URL)
cache_mgr = get_cache_manager(config.REDIS_URL)

from pydantic import BaseModel

class SimpleNotificationRequest(BaseModel):
    user_id: UUID = Field(..., alias="id") # Accept 'id' from client, map to 'user_id' internally
    template_code: str
    variables: Dict[str, Any]
    priority: str = "normal"

@router.post("/email", response_model=schemas.APIResponse[schemas.NotificationResponse], status_code=status.HTTP_201_CREATED)
def send_email_notification(
    request: SimpleNotificationRequest,
    db: Session = Depends(get_db)
):
    """Convenience endpoint to send email notifications"""
    # Map priority string to int
    priority_map = {"low": 0, "normal": 0, "high": 1, "urgent": 2}
    priority_int = priority_map.get(request.priority.lower(), 0)
    
    # Create notification request
    notification = schemas.NotificationRequest(
        notification_type=schemas.NotificationType.email,
        user_id=request.user_id,
        template_code=request.template_code,
        variables=request.variables,
        request_id=str(uuid.uuid4()),
        priority=priority_int
    )
    
    # Use the existing send_notification function, generate correlation_id here
    return send_notification(notification, db, correlation_id=str(uuid.uuid4()))


@router.post("/push", response_model=schemas.APIResponse[schemas.NotificationResponse], status_code=status.HTTP_201_CREATED)
def send_push_notification(
    request: SimpleNotificationRequest,
    db: Session = Depends(get_db)
):
    """Convenience endpoint to send push notifications"""
    # Map priority string to int
    priority_map = {"low": 0, "normal": 0, "high": 1, "urgent": 2}
    priority_int = priority_map.get(request.priority.lower(), 0)
    
    # Create notification request
    notification = schemas.NotificationRequest(
        notification_type=schemas.NotificationType.push,
        user_id=request.user_id,
        template_code=request.template_code,
        variables=request.variables,
        request_id=str(uuid.uuid4()),
        priority=priority_int
    )
    
    # Use the existing send_notification function, generate correlation_id here
    return send_notification(notification, db, correlation_id=str(uuid.uuid4()))


@router.post("/send", response_model=schemas.APIResponse[schemas.NotificationResponse], status_code=status.HTTP_201_CREATED)
def send_notification(
    notification: schemas.NotificationRequest,
    db: Session = Depends(get_db),
    correlation_id: Optional[str] = None,
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
):
    """Send a notification (email or push)"""
    # Use provided correlation_id, or from header, or generate new one
    if correlation_id is None:
        correlation_id = x_correlation_id if x_correlation_id else str(uuid.uuid4())
    request_id = notification.request_id
    
    logger.info(f"Received notification request: {request_id}, type: {notification.notification_type}")
    
    # Idempotency check - cache first, then DB
    if cache_mgr.check_idempotency(request_id):
        logger.info(f"Duplicate request detected in cache: {request_id}")
        # Return existing notification from DB
        existing = db.query(models.NotificationRequest).filter(
            models.NotificationRequest.request_id == request_id
        ).first()
        if existing:
            return schemas.APIResponse(
                data=existing,
                message="Notification already processed (idempotent request)"
            )
    
    # Check DB for duplicate (in case cache expired)
    existing = db.query(models.NotificationRequest).filter(
        models.NotificationRequest.request_id == request_id
    ).first()
    if existing:
        logger.info(f"Duplicate request detected in DB: {request_id}")
        # Update cache
        cache_mgr.set_idempotency(request_id, ttl=86400)
        return schemas.APIResponse(
            data=existing,
            message="Notification already processed (idempotent request)"
        )
    
    # Rate limiting check (100 requests per minute per user)
    rate_limit_key = f"rate_limit:user:{notification.user_id}"
    if not cache_mgr.rate_limit_check(rate_limit_key, limit=100, window=60):
        logger.warning(f"Rate limit exceeded for user {notification.user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Validate user exists and get recipient (with caching)
    user_cache_key = f"user:{notification.user_id}"
    user_data = cache_mgr.get(user_cache_key)
    
    if not user_data:
        try:
            response = requests.get(
                f"{config.USER_SERVICE_URL}/api/v1/users/{notification.user_id}",
                timeout=5
            )
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="User not found")
            response.raise_for_status()
            user_response_data = response.json()
            # Assuming the user data is in the 'data' field of the response, which is a list
            if user_response_data and user_response_data.get("data") and len(user_response_data["data"]) > 0:
                user_data = user_response_data["data"][0]
                cache_mgr.set(user_cache_key, user_data, ttl=300)
            else:
                raise HTTPException(status_code=404, detail="User data not found in response")
        except requests.RequestException as e:
            logger.error(f"Error fetching user data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service unavailable"
            )
    
    # Determine recipient based on notification type
    recipient = None
    if notification.notification_type == schemas.NotificationType.email:
        recipient = user_data.get("email")
    elif notification.notification_type == schemas.NotificationType.push:
        recipient = user_data.get("push_token")
    
    if not recipient:
        raise HTTPException(
            status_code=400, 
            detail=f"No {notification.notification_type.value} recipient found for user"
        )
    
    # Create notification record
    db_notification = models.NotificationRequest(
        request_id=request_id,
        correlation_id=correlation_id,
        user_id=notification.user_id,
        notification_type=notification.notification_type.value,
        template_code=notification.template_code,
        recipient=recipient,
        variables=notification.variables,  # Already a dict
        status=models.NotificationStatus.pending,
        priority=notification.priority,
        extra_metadata=notification.extra_metadata
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Publish to appropriate queue
    try:
        routing_key = notification.notification_type.value  # 'email' or 'push'
        message = {
            "notification_id": db_notification.id,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "user_id": str(notification.user_id),
            "notification_type": notification.notification_type.value,
            "template_code": notification.template_code,
            "recipient": recipient,
            "variables": notification.variables,  # Already a dict
            "priority": notification.priority,
            "extra_metadata": notification.extra_metadata,
            "retry_count": 0
        }
        
        queue_mgr.publish_message(
            exchange=config.EXCHANGE_NAME,
            routing_key=routing_key,
            message=message,
            correlation_id=correlation_id
        )
        
        # Mark as processed for idempotency
        cache_mgr.set_idempotency(request_id, ttl=86400)  # 24 hours
        
        logger.info(f"Notification queued successfully: {request_id}")
        
    except Exception as e:
        logger.error(f"Error publishing to queue: {str(e)}")
        db_notification.status = models.NotificationStatus.failed
        db_notification.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to queue notification"
        )
    
    return schemas.APIResponse(
        data=db_notification,
        message="Notification queued successfully"
    )

@router.post("/send/bulk", response_model=schemas.APIResponse[List[schemas.NotificationResponse]], status_code=status.HTTP_201_CREATED)
def send_bulk_notifications(
    bulk_request: schemas.BulkNotificationRequest,
    db: Session = Depends(get_db),
    x_correlation_id: Optional[str] = Header(None)
):
    """Send bulk notifications to multiple users"""
    correlation_id = x_correlation_id or str(uuid.uuid4())
    
    logger.info(f"Received bulk notification request for {len(bulk_request.user_ids)} users")
    
    notifications = []
    failed = []
    
    for user_id in bulk_request.user_ids:
        try:
            # Get user data
            user_cache_key = f"user:{user_id}"
            user_data = cache_mgr.get(user_cache_key)
            
            if not user_data:
                response = requests.get(
                    f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}",
                    timeout=5
                )
                if response.status_code == 404:
                    failed.append({"user_id": str(user_id), "error": "User not found"})
                    continue
                user_response_data = response.json()
                if user_response_data and user_response_data.get("data") and len(user_response_data["data"]) > 0:
                    user_data = user_response_data["data"][0]
                    cache_mgr.set(user_cache_key, user_data, ttl=300)
                else:
                    failed.append({"user_id": str(user_id), "error": "User data not found in response"})
                    continue
            
            # Create individual notification request
            notification = schemas.NotificationRequest(
                notification_type=bulk_request.notification_type,
                user_id=user_id,
                template_code=bulk_request.template_code,
                variables=bulk_request.variables,
                request_id=str(uuid.uuid4()),
                priority=0
            )
            
            # Send notification
            result = send_notification(notification, db, correlation_id)
            notifications.append(result.data)
            
        except Exception as e:
            logger.error(f"Error sending to user {user_id}: {str(e)}")
            failed.append({"user_id": str(user_id), "error": str(e)})
    
    logger.info(f"Bulk send completed: {len(notifications)} successful, {len(failed)} failed")
    
    return schemas.APIResponse(
        data=notifications,
        message=f"Sent {len(notifications)} notifications, {len(failed)} failed",
        meta=schemas.PaginationMeta(
            total=len(bulk_request.user_ids),
            limit=len(bulk_request.user_ids),
            page=1,
            total_pages=1,
            has_next=False,
            has_previous=False
        )
    )

@router.get("/{notification_id}", response_model=schemas.APIResponse[schemas.NotificationResponse])
def get_notification_status(notification_id: int, db: Session = Depends(get_db)):
    """Get notification status by ID"""
    notification = db.query(models.NotificationRequest).filter(
        models.NotificationRequest.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return schemas.APIResponse(
        data=notification,
        message="Notification retrieved successfully"
    )

@router.get("/request/{request_id}", response_model=schemas.APIResponse[schemas.NotificationResponse])
def get_notification_by_request_id(request_id: str, db: Session = Depends(get_db)):
    """Get notification by request ID (for idempotency tracking)"""
    notification = db.query(models.NotificationRequest).filter(
        models.NotificationRequest.request_id == request_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return schemas.APIResponse(
        data=notification,
        message="Notification retrieved successfully"
    )

@router.get("/user/{user_id}", response_model=schemas.APIResponse[List[schemas.NotificationResponse]])
def get_user_notifications(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    notification_type: Optional[str] = None,
    status: Optional[schemas.NotificationStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all notifications for a user"""
    query = db.query(models.NotificationRequest).filter(
        models.NotificationRequest.user_id == user_id
    )
    
    if notification_type:
        query = query.filter(models.NotificationRequest.notification_type == notification_type)
    if status:
        query = query.filter(models.NotificationRequest.status == status.value)
    
    total = query.count()
    notifications = query.order_by(desc(models.NotificationRequest.created_at)).offset(skip).limit(limit).all()
    
    # Calculate pagination meta
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1
    
    meta = schemas.PaginationMeta(
        total=total,
        limit=limit,
        page=current_page,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_previous=current_page > 1
    )
    
    return schemas.APIResponse(
        data=notifications,
        message="Notifications retrieved successfully",
        meta=meta
    )

@router.post("/{notification_type}/status", response_model=schemas.APIResponse[schemas.NotificationResponse])
def update_notification_status(
    notification_type: str,
    status_update: schemas.NotificationStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update notification status (used by worker services)"""
    try:
        notification_id = int(status_update.notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification_id format")
    
    notification = db.query(models.NotificationRequest).filter(
        models.NotificationRequest.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.status = status_update.status
    if status_update.error:
        notification.error_message = status_update.error
    
    if status_update.status == schemas.NotificationStatus.delivered:
        notification.sent_at = status_update.timestamp or datetime.utcnow()
    
    db.commit()
    db.refresh(notification)
    
    logger.info(f"Notification {notification_id} status updated to {status_update.status}")
    
    return schemas.APIResponse(
        data=notification,
        message="Notification status updated successfully"
    )


# ============================================
# User Management Proxy Routes
# ============================================

@user_router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user_data: dict):
    """Proxy request to User Service - Create a new user"""
    try:
        response = requests.post(
            f"{config.USER_SERVICE_URL}/api/v1/users",
            json=user_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.get("/users/{user_id}")
def get_user(user_id: str):
    """Proxy request to User Service - Get user by ID"""
    try:
        response = requests.get(
            f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.get("/users")
def list_users():
    """Proxy request to User Service - List all users"""
    try:
        response = requests.get(
            f"{config.USER_SERVICE_URL}/api/v1/users",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.put("/users/{user_id}")
def update_user(user_id: str, user_data: dict):
    """Proxy request to User Service - Update user"""
    try:
        response = requests.put(
            f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}",
            json=user_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.get("/users/{user_id}/preferences")
def get_user_preferences(user_id: str):
    """Proxy request to User Service - Get user notification preferences"""
    try:
        response = requests.get(
            f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}/preferences",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.put("/users/{user_id}/preferences")
def update_user_preferences(user_id: str, preference_data: dict):
    """Proxy request to User Service - Update user notification preferences"""
    try:
        response = requests.put(
            f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}/preferences",
            json=preference_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


@user_router.put("/users/{user_id}/push-token")
def update_push_token(user_id: str, token_data: dict):
    """Proxy request to User Service - Update user push notification token"""
    try:
        response = requests.put(
            f"{config.USER_SERVICE_URL}/api/v1/users/{user_id}/push-token",
            json=token_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update push token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"User service error: {str(e)}")


# ============================================
# Template Management Proxy Routes
# ============================================

@template_router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(template_data: dict):
    """Proxy request to Template Service - Create a new template"""
    try:
        response = requests.post(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates",
            json=template_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.get("/templates/{template_id}")
def get_template(template_id: str):
    """Proxy request to Template Service - Get template by ID"""
    try:
        response = requests.get(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates/{template_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.get("/templates")
def list_templates():
    """Proxy request to Template Service - List all templates"""
    try:
        response = requests.get(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to list templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.get("/templates/code/{code}")
def get_template_by_code(code: str):
    """Proxy request to Template Service - Get template by code"""
    try:
        response = requests.get(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates/code/{code}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get template by code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.put("/templates/{template_id}")
def update_template(template_id: str, template_data: dict):
    """Proxy request to Template Service - Update template"""
    try:
        response = requests.put(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates/{template_id}",
            json=template_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.delete("/templates/{template_id}")
def delete_template(template_id: str):
    """Proxy request to Template Service - Delete template"""
    try:
        response = requests.delete(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates/{template_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to delete template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")


@template_router.post("/templates/render")
def render_template(render_data: dict):
    """Proxy request to Template Service - Render template with variables"""
    try:
        response = requests.post(
            f"{config.TEMPLATE_SERVICE_URL}/api/v1/templates/render",
            json=render_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to render template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Template service error: {str(e)}")
