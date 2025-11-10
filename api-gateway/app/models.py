from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

class NotificationStatus(str, Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"

class NotificationRequest(Base):
    __tablename__ = "notification_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, nullable=False)  # For idempotency
    correlation_id = Column(String, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    notification_type = Column(String, nullable=False)  # 'email', 'push'
    template_code = Column(String, nullable=False)
    recipient = Column(String, nullable=False)  # Email address or device token
    variables = Column(JSON, default=dict, nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.pending, nullable=False)
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # 0=normal, 1=high, 2=urgent
    extra_metadata = Column(JSON, default=dict, nullable=True)  # renamed from 'metadata' (SQLAlchemy reserved word)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<NotificationRequest(id={self.id}, request_id={self.request_id}, status={self.status})>"
