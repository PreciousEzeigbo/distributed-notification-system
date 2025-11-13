from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from typing import TypeVar, Generic
from uuid import UUID

T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total number of items", example=100)
    limit: int = Field(..., description="Number of items per page", example=10)
    page: int = Field(..., description="Current page number", example=1)
    total_pages: int = Field(..., description="Total number of pages", example=10)
    has_next: bool = Field(..., description="Whether there is a next page", example=True)
    has_previous: bool = Field(..., description="Whether there is a previous page", example=False)

class APIResponse(BaseModel, Generic[T]):
    success: bool = Field(True, description="Indicates if the operation was successful", example=True)
    message: str = Field("Operation successful", description="Human-readable message about the operation", example="Notification created successfully")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[str] = Field(None, description="Error message if operation failed", example=None)
    meta: Optional[PaginationMeta] = Field(None, description="Pagination metadata", example=None)

class NotificationType(str, Enum):
    """Notification channel types"""
    email = "email"
    push = "push"

class NotificationStatus(str, Enum):
    """Notification delivery status"""
    pending = "pending"
    delivered = "delivered"
    failed = "failed"

class NotificationRequest(BaseModel):
    notification_type: NotificationType = Field(
        ..., 
        description="Type of notification to send (email or push)",
        example="email"
    )
    user_id: UUID = Field(
        ..., 
        description="Unique identifier of the recipient user",
        example="123e4567-e89b-12d3-a456-426614174000"
    )
    template_code: str = Field(
        ..., 
        description="Code of the template to use for the notification",
        example="welcome_email"
    )
    variables: Dict[str, Any] = Field(
        ..., 
        description="Variables to substitute in the template",
        example={"name": "John Doe", "email": "john@example.com"}
    )
    request_id: str = Field(
        ..., 
        description="Unique identifier for idempotency (prevents duplicate sends)",
        example="req_123e4567"
    )
    priority: int = Field(
        0, 
        description="Notification priority (0=normal, 1=high, 2=urgent)",
        example=0,
        ge=0,
        le=2
    )
    extra_metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for tracking or analytics",
        example={"campaign_id": "summer_2025", "source": "web"}
    )

class NotificationResponse(BaseModel):
    id: int = Field(..., description="Notification database ID", example=1)
    request_id: str = Field(..., description="Request ID for idempotency tracking", example="req_123e4567")
    correlation_id: str = Field(..., description="Correlation ID for distributed tracing", example="corr_123e4567")
    user_id: UUID = Field(..., description="User ID of the recipient", example="123e4567-e89b-12d3-a456-426614174000")
    notification_type: str = Field(..., description="Type of notification (email or push)", example="email")
    template_code: str = Field(..., description="Template code used", example="welcome_email")
    recipient: str = Field(..., description="Recipient address (email or push token)", example="user@example.com")
    status: NotificationStatus = Field(..., description="Current delivery status", example="pending")
    error_message: Optional[str] = Field(None, description="Error message if failed", example=None)
    retry_count: int = Field(..., description="Number of retry attempts", example=0)
    priority: int = Field(..., description="Notification priority", example=0)
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata", example=None)
    created_at: datetime = Field(..., description="Timestamp when notification was created", example="2025-11-13T09:00:00Z")
    updated_at: datetime = Field(..., description="Timestamp when notification was last updated", example="2025-11-13T09:00:00Z")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when notification was sent", example=None)

    class Config:
        from_attributes = True
        orm_mode = True

class NotificationStatusUpdate(BaseModel):
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

class BulkNotificationRequest(BaseModel):
    user_ids: List[UUID] = Field(
        ..., 
        description="List of user IDs to send notification to",
        example=["123e4567-e89b-12d3-a456-426614174000", "223e4567-e89b-12d3-a456-426614174001"]
    )
    notification_type: NotificationType = Field(
        ..., 
        description="Type of notification to send (email or push)",
        example="email"
    )
    template_code: str = Field(
        ..., 
        description="Code of the template to use",
        example="welcome_email"
    )
    variables: Dict[str, Any] = Field(
        ..., 
        description="Variables to substitute in the template (same for all users)",
        example={"campaign": "Summer Sale", "discount": "20%"}
    )


