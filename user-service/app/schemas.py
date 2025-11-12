from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from typing import TypeVar, Generic, List
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

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class UserPreference(BaseModel):
    """User notification preferences"""
    email: bool = True
    push: bool = True

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    push_token: Optional[str] = None
    preferences: UserPreference = Field(default_factory=lambda: UserPreference())

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    push_token: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FCMTokenRequest(BaseModel):
    """Request body for registering FCM token"""
    fcm_token: str = Field(..., min_length=1, description="Firebase Cloud Messaging device token")

class UserResponse(UserBase):
    id: UUID
    push_token: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True

class NotificationPreferenceBase(BaseModel):
    channel: str  # 'email', 'push', 'sms'
    enabled: bool = True
    preferences: Optional[Dict[str, Any]] = {}

class NotificationPreferenceCreate(NotificationPreferenceBase):
    pass

class NotificationPreferenceUpdate(BaseModel):
    enabled: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True