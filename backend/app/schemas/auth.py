from pydantic import EmailStr, Field
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime

from app.schemas.base import AppBaseModel, TimestampMixin


class SignUpRequest(AppBaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    user_type: Literal["organization", "candidate", "admin"] = Field(..., description="Type of user")
    full_name: Optional[str] = Field(default=None, description="Full name of the user")


class SignInRequest(AppBaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class GoogleAuthRequest(AppBaseModel):
    user_type: Literal["organization", "candidate", "admin"] = Field(..., description="Type of user for Google signup")


class TokenResponse(AppBaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Token expiry in seconds")
    expires_at: Optional[int] = Field(default=None, description="Token expiry timestamp")


class UserProfile(AppBaseModel, TimestampMixin):
    id: UUID
    email: EmailStr
    user_type: Literal["organization", "candidate", "admin"]
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_confirmed_at: Optional[datetime] = None


class AuthResponse(AppBaseModel):
    user: UserProfile
    session: TokenResponse


class GoogleAuthUrlResponse(AppBaseModel):
    url: str = Field(..., description="Google OAuth authorization URL")


class RefreshTokenRequest(AppBaseModel):
    refresh_token: str = Field(..., description="Refresh token to get new access token")


class PasswordResetRequest(AppBaseModel):
    email: EmailStr = Field(..., description="Email to send password reset link")


class PasswordUpdateRequest(AppBaseModel):
    password: str = Field(..., min_length=8, description="New password (min 8 characters)")
