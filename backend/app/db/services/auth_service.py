from typing import Optional
from uuid import UUID

from passlib.context import CryptContext

from app.db.connection import get_async_supabase_client
from app.config.logging import get_logger
from app.schemas.auth import (
    SignUpRequest, SignInRequest, AuthResponse, 
    UserProfile, TokenResponse
)

logger = get_logger("db.services.auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    async def sign_up(self, request: SignUpRequest) -> AuthResponse:
        client = await get_async_supabase_client()
        
        response = await client.auth_sign_up(
            email=request.email,
            password=request.password,
            data={
                "full_name": request.full_name,
                "user_type": request.user_type
            }
        )
        
        logger.info(f"User signed up: {request.email}, type: {request.user_type}")
        
        return self._build_auth_response(response)
    
    async def sign_in(self, request: SignInRequest) -> AuthResponse:
        client = await get_async_supabase_client()
        
        response = await client.auth_sign_in(
            email=request.email,
            password=request.password
        )
        
        logger.info(f"User signed in: {request.email}")
        
        return self._build_auth_response(response)
    
    async def sign_out(self, access_token: str) -> bool:
        client = await get_async_supabase_client()
        await client.auth_sign_out(access_token)
        logger.info("User signed out")
        return True
    
    async def get_google_auth_url(self, user_type: str, redirect_url: str) -> str:
        client = await get_async_supabase_client()
        url = client.get_oauth_url(
            provider="google",
            redirect_to=redirect_url
        )
        logger.info(f"Google OAuth URL generated for user_type: {user_type}")
        return url
    
    async def handle_google_callback(self, code: str) -> AuthResponse:
        client = await get_async_supabase_client()
        response = await client.auth_exchange_code(code)
        logger.info("Google auth successful")
        return self._build_auth_response(response)
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        client = await get_async_supabase_client()
        response = await client.auth_refresh_token(refresh_token)
        
        logger.info("Token refreshed successfully")
        
        return TokenResponse(
            access_token=response.get("access_token"),
            refresh_token=response.get("refresh_token"),
            token_type="bearer",
            expires_in=response.get("expires_in", 3600),
            expires_at=response.get("expires_at")
        )
    
    async def get_current_user(self, access_token: str) -> Optional[UserProfile]:
        client = await get_async_supabase_client()
        
        try:
            user_data = await client.auth_get_user(access_token)
        except Exception:
            return None
        
        user_metadata = user_data.get("user_metadata", {})
        
        return UserProfile(
            id=UUID(user_data["id"]),
            email=user_data["email"],
            user_type=user_metadata.get("user_type", "candidate"),
            full_name=user_metadata.get("full_name"),
            avatar_url=user_metadata.get("avatar_url"),
            email_confirmed_at=user_data.get("email_confirmed_at"),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
    
    async def reset_password(self, email: str, redirect_url: str) -> bool:
        client = await get_async_supabase_client()
        await client.auth_reset_password(email, redirect_url)
        logger.info(f"Password reset email sent to: {email}")
        return True
    
    async def update_password(self, access_token: str, new_password: str) -> bool:
        client = await get_async_supabase_client()
        await client.auth_update_user(access_token, {"password": new_password})
        logger.info("Password updated successfully")
        return True
    
    def _build_auth_response(self, response: dict) -> AuthResponse:
        user = response.get("user", response)
        user_metadata = user.get("user_metadata", {})
        
        return AuthResponse(
            user=UserProfile(
                id=UUID(user["id"]),
                email=user["email"],
                user_type=user_metadata.get("user_type", "candidate"),
                full_name=user_metadata.get("full_name"),
                avatar_url=user_metadata.get("avatar_url"),
                email_confirmed_at=user.get("email_confirmed_at"),
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at")
            ),
            session=TokenResponse(
                access_token=response.get("access_token", ""),
                refresh_token=response.get("refresh_token", ""),
                token_type="bearer",
                expires_in=response.get("expires_in", 3600),
                expires_at=response.get("expires_at")
            )
        )


auth_service = AuthService()
