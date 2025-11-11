from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from typing import TypeVar, Generic
from uuid import UUID

T = TypeVar("T")

class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[PaginationMeta] = None

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
    notification_type: NotificationType
    user_id: UUID
    template_code: str  # Template name or path
    variables: Dict[str, Any]  # Generic dict for template variables
    request_id: str
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    extra_metadata: Optional[Dict[str, Any]] = None  # renamed from 'metadata' (SQLAlchemy reserved word)

class NotificationResponse(BaseModel):
    id: int
    request_id: str
    correlation_id: str
    user_id: UUID
    notification_type: str
    template_code: str
    recipient: str
    status: NotificationStatus
    error_message: Optional[str] = None
    retry_count: int
    priority: int
    extra_metadata: Optional[Dict[str, Any]] = None  # renamed from 'metadata' (SQLAlchemy reserved word)
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True

class NotificationStatusUpdate(BaseModel):
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

class BulkNotificationRequest(BaseModel):
    user_ids: List[UUID]
    notification_type: NotificationType
    template_code: str
    variables: Dict[str, Any]  # Generic dict for template variables


