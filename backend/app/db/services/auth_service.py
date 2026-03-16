"""
Authentication service – local JWT + SQLAlchemy implementation.

Sign-up / sign-in create rows in the `users` table and return
locally-minted JWT access + refresh tokens.  No external auth
provider (Supabase Auth, etc.) is required.
"""
from typing import Optional

from sqlalchemy import select
import bcrypt

from app.config.settings import get_settings
from app.config.logging import get_logger
from app.db.session import get_session_maker
from app.db.models.user import User, UserType
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
)
from app.schemas.auth import (
    SignUpRequest,
    SignInRequest,
    AuthResponse,
    UserProfile,
    TokenResponse,
)

logger = get_logger("db.services.auth")



class AuthService:
    """Handles user registration, login, token refresh, and profile lookup."""

    # ── password helpers ──────────────────────────────────────────
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    # ── helpers ───────────────────────────────────────────────────
    def _build_tokens(self, user: User) -> TokenResponse:
        """Create an access + refresh token pair for *user*."""
        settings = get_settings()
        user_type = user.user_type.value if isinstance(user.user_type, UserType) else str(user.user_type)
        access = create_access_token(subject=str(user.id), user_type=user_type)
        refresh = create_refresh_token(subject=str(user.id))
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    @staticmethod
    def _user_to_profile(user: User) -> UserProfile:
        user_type = user.user_type.value if isinstance(user.user_type, UserType) else str(user.user_type)
        return UserProfile(
            id=str(user.id),
            email=user.email,
            user_type=user_type,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            email_confirmed_at=None,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    # ── public API ────────────────────────────────────────────────
    async def sign_up(self, request: SignUpRequest) -> AuthResponse:
        session_maker = get_session_maker()
        async with session_maker() as session:
            # Check if email already exists
            result = await session.execute(
                select(User).where(User.email == request.email)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError("A user with this email already exists")

            user = User(
                email=request.email,
                password_hash=self.hash_password(request.password),
                full_name=request.full_name,
                user_type=request.user_type,  # stored as plain string
                provider="email",
                email_verified="N",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"User signed up: {request.email}, type: {request.user_type}")
            return AuthResponse(
                user=self._user_to_profile(user),
                session=self._build_tokens(user),
            )

    async def sign_in(self, request: SignInRequest) -> AuthResponse:
        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == request.email)
            )
            user = result.scalar_one_or_none()

            if user is None:
                raise ValueError("Invalid email or password")

            if not user.password_hash:
                raise ValueError("This account uses OAuth login. Please sign in with Google.")

            if not self.verify_password(request.password, user.password_hash):
                raise ValueError("Invalid email or password")

            logger.info(f"User signed in: {request.email}")
            return AuthResponse(
                user=self._user_to_profile(user),
                session=self._build_tokens(user),
            )

    async def sign_out(self, access_token: str) -> bool:
        """
        With stateless JWTs there's nothing to invalidate server-side.
        The client simply discards the token.
        """
        logger.info("User signed out (client-side token discard)")
        return True

    async def refresh_token(self, token: str) -> TokenResponse:
        payload = verify_refresh_token(token)
        if payload is None:
            raise ValueError("Invalid or expired refresh token")

        user_id = payload["sub"]

        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("User not found")

            return self._build_tokens(user)

    async def get_current_user(self, access_token: str) -> Optional[UserProfile]:
        payload = verify_access_token(access_token)
        if payload is None:
            return None

        user_id = payload["sub"]

        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                return None

            return self._user_to_profile(user)

    async def reset_password(self, email: str, redirect_url: str) -> bool:
        """
        Placeholder – in production send an email with a signed reset-link.
        For now we just verify the user exists.
        """
        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            if user is None:
                logger.info(f"Password reset requested for unknown email: {email}")
            else:
                logger.info(f"Password reset requested for: {email}")
        return True

    async def update_password(self, access_token: str, new_password: str) -> bool:
        payload = verify_access_token(access_token)
        if payload is None:
            raise ValueError("Invalid or expired token")

        user_id = payload["sub"]

        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("User not found")

            user.password_hash = self.hash_password(new_password)
            await session.commit()
            logger.info("Password updated successfully")
        return True

    async def get_google_auth_url(self, user_type: str, redirect_url: str) -> str:
        """Generate a Supabase-style Google OAuth URL (kept for compatibility)."""
        from app.db.connection import get_async_supabase_client
        client = await get_async_supabase_client()
        url = client.get_oauth_url(provider="google", redirect_to=redirect_url)
        logger.info(f"Google OAuth URL generated for user_type: {user_type}")
        return url

    async def handle_google_callback(self, code: str) -> AuthResponse:
        """Exchange Google OAuth code via Supabase and upsert local user."""
        from app.db.connection import get_async_supabase_client
        client = await get_async_supabase_client()
        response = await client.auth_exchange_code(code)

        supa_user = response.get("user", response)
        metadata = supa_user.get("user_metadata", {})
        email = supa_user.get("email") or metadata.get("email")

        session_maker = get_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if user is None:
                user = User(
                    email=email,
                    full_name=metadata.get("full_name") or metadata.get("name"),
                    avatar_url=metadata.get("avatar_url") or metadata.get("picture"),
                    user_type=metadata.get("user_type", "candidate"),
                    provider="google",
                    provider_id=supa_user.get("id"),
                    email_verified="Y",
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            logger.info(f"Google auth successful for: {email}")
            return AuthResponse(
                user=self._user_to_profile(user),
                session=self._build_tokens(user),
            )


auth_service = AuthService()
