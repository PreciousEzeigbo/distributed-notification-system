"""Standard API response format"""
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar('T')

class PaginationMeta(BaseModel):
    total: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    message: str = "Success"
    meta: Optional[PaginationMeta] = None

    class Config:
        from_attributes = True
