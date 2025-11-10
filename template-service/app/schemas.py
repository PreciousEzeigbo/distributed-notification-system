from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from typing import TypeVar, Generic

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

class TemplateBase(BaseModel):
    name: str
    channel: str  # 'email', 'push', 'sms'
    language: str = "en"
    subject: Optional[str] = None
    body: str
    variables: List[str] = []

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    channel: Optional[str] = None
    language: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TemplateResponse(TemplateBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True

class TemplateVersionResponse(BaseModel):
    id: int
    template_id: int
    version: int
    subject: Optional[str] = None
    body: str
    variables: List[str]
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True

class TemplateRenderRequest(BaseModel):
    template_name: str
    language: str = "en"
    variables: Dict[str, Any]

class TemplateRenderResponse(BaseModel):
    subject: Optional[str] = None
    body: str
    rendered: bool = True
