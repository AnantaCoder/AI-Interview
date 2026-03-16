from fastapi import APIRouter, HTTPException, Query, Depends

from app.db.services.auth_service import auth_service
from app.deps import get_current_user, bearer_scheme
from app.schemas.auth import (
    SignUpRequest, SignInRequest, AuthResponse,
    GoogleAuthRequest, GoogleAuthUrlResponse, TokenResponse,
    RefreshTokenRequest, PasswordResetRequest, PasswordUpdateRequest,
    UserProfile,
)
from app.schemas.responses import ApiResponse
from app.config.settings import get_settings
from app.config.logging import get_logger
from app.utils.security import verify_access_token
from fastapi.security import HTTPAuthorizationCredentials

logger = get_logger("routers.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    summary="User signup",
    description="Register a new user (organization or candidate) with email and password.",
)
async def signup(request: SignUpRequest) -> AuthResponse:
    try:
        return await auth_service.sign_up(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail="Signup failed due to an internal error")


@router.post(
    "/signin",
    response_model=AuthResponse,
    summary="User signin",
    description="Authenticate user with email and password. Returns JWT access and refresh tokens.",
)
async def signin(request: SignInRequest) -> AuthResponse:
    try:
        return await auth_service.sign_in(request)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Signin failed: {e}")
        raise HTTPException(status_code=500, detail="Signin failed due to an internal error")


@router.post(
    "/signout",
    response_model=ApiResponse,
    summary="User signout",
    description="Sign out the current user (client should discard tokens).",
)
async def signout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> ApiResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        await auth_service.sign_out(credentials.credentials)
        return ApiResponse(success=True, message="Signed out successfully")
    except Exception as e:
        logger.error(f"Signout failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/google",
    response_model=GoogleAuthUrlResponse,
    summary="Get Google OAuth URL",
    description="Generate Google OAuth authorization URL for signup/signin.",
)
async def google_auth_url(
    user_type: str = Query(..., description="User type: organization, candidate or admin"),
) -> GoogleAuthUrlResponse:
    settings = get_settings()
    try:
        url = await auth_service.get_google_auth_url(
            user_type=user_type,
            redirect_url=settings.google_redirect_uri,
        )
        return GoogleAuthUrlResponse(url=url)
    except Exception as e:
        logger.error(f"Google auth URL generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/callback/google",
    summary="Google OAuth callback",
    description="Handle Google OAuth callback and exchange code for session.",
)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
) -> AuthResponse:
    try:
        return await auth_service.handle_google_callback(code)
    except Exception as e:
        logger.error(f"Google callback failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using the refresh token.",
)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    try:
        return await auth_service.refresh_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
)
async def get_me(
    user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    return user


@router.post(
    "/password/reset",
    response_model=ApiResponse,
    summary="Request password reset",
    description="Send a password reset email to the user.",
)
async def request_password_reset(request: PasswordResetRequest) -> ApiResponse:
    settings = get_settings()
    try:
        await auth_service.reset_password(
            email=request.email,
            redirect_url=f"{settings.cors_origins[0]}/reset-password",
        )
        return ApiResponse(success=True, message="Password reset email sent")
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/password/update",
    response_model=ApiResponse,
    summary="Update password",
    description="Update the password for the authenticated user.",
)
async def update_password(
    body: PasswordUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> ApiResponse:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        await auth_service.update_password(credentials.credentials, body.password)
        return ApiResponse(success=True, message="Password updated successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
