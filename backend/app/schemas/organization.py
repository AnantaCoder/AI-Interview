from pydantic import EmailStr, Field
from typing import Optional
from uuid import UUID

from app.schemas.base import AppBaseModel, TimestampMixin, IdMixin


class OrganizationBase(AppBaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    description: Optional[str] = Field(default=None, description="Organization description")
    website: Optional[str] = Field(default=None, description="Organization website URL")
    industry: Optional[str] = Field(default=None, description="Industry sector")
    logo_url: Optional[str] = Field(default=None, description="Organization logo URL")


class OrganizationCreate(OrganizationBase):
    user_id: UUID = Field(..., description="Associated auth user ID")
    contact_email: EmailStr = Field(..., description="Contact email")


class OrganizationUpdate(AppBaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    contact_email: Optional[EmailStr] = None


class OrganizationResponse(OrganizationBase, IdMixin, TimestampMixin):
    user_id: UUID
    contact_email: EmailStr
    is_active: bool = Field(default=True)
