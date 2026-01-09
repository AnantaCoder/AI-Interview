from pydantic import Field
from typing import Optional, Any, Generic, TypeVar
from app.schemas.base import AppBaseModel

T = TypeVar("T")


class ApiResponse(AppBaseModel, Generic[T]):
    success: bool = Field(default=True)
    message: str = Field(default="Operation successful")
    data: Optional[T] = None


class ErrorResponse(AppBaseModel):
    success: bool = Field(default=False)
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Application error code")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")


class PaginatedResponse(AppBaseModel, Generic[T]):
    success: bool = Field(default=True)
    data: list[T] = Field(default_factory=list)
    total: int = Field(default=0, description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=10, description="Items per page")
    total_pages: int = Field(default=0, description="Total number of pages")


class HealthResponse(AppBaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    database: Optional[str] = Field(default=None, description="Database connection status")
