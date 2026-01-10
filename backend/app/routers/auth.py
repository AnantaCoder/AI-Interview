from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app.db.services.auth_service import auth_service
from app.schemas.auth import (
    SignUpRequest, SignInRequest, AuthResponse, 
    GoogleAuthRequest, GoogleAuthUrlResponse, TokenResponse,
    RefreshTokenRequest, PasswordResetRequest, PasswordUpdateRequest,
    UserProfile
)
from app.schemas.responses import ApiResponse
from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("routers.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    summary="User signup",
    description="Register a new user (organization or candidate) with email and password."
)
async def signup(request: SignUpRequest) -> AuthResponse:
    try:
        return await auth_service.sign_up(request)
    except Exception as e:
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/signin",
    response_model=AuthResponse,
    summary="User signin",
    description="Authenticate user with email and password."
)
async def signin(request: SignInRequest) -> AuthResponse:
    try:
        return await auth_service.sign_in(request)
    except Exception as e:
        logger.error(f"Signin failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post(
    "/signout",
    response_model=ApiResponse,
    summary="User signout",
    description="Sign out the current user and invalidate the session."
)
async def signout(request: Request) -> ApiResponse:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    
    try:
        await auth_service.sign_out(token)
        return ApiResponse(success=True, message="Signed out successfully")
    except Exception as e:
        logger.error(f"Signout failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/google",
    response_model=GoogleAuthUrlResponse,
    summary="Get Google OAuth URL",
    description="Generate Google OAuth authorization URL for signup/signin."
)
async def google_auth_url(
    user_type: str = Query(..., description="User type: organization, candidate or admin")
) -> GoogleAuthUrlResponse:
    settings = get_settings()
    
    try:
        url = await auth_service.get_google_auth_url(
            user_type=user_type,
            redirect_url=settings.google_redirect_uri
        )
        return GoogleAuthUrlResponse(url=url)
    except Exception as e:
        logger.error(f"Google auth URL generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/callback/google",
    summary="Google OAuth callback",
    description="Handle Google OAuth callback and exchange code for session."
)
async def google_callback(
    code: str = Query(..., description="Authorization code from Google")
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
    description="Get a new access token using the refresh token."
)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    try:
        return await auth_service.refresh_token(request.refresh_token)
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get current user",
    description="Get the profile of the currently authenticated user."
)
async def get_current_user(request: Request) -> UserProfile:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    
    try:
        user = await auth_service.get_current_user(token)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post(
    "/password/reset",
    response_model=ApiResponse,
    summary="Request password reset",
    description="Send a password reset email to the user."
)
async def request_password_reset(request: PasswordResetRequest) -> ApiResponse:
    settings = get_settings()
    
    try:
        await auth_service.reset_password(
            email=request.email,
            redirect_url=f"{settings.cors_origins[0]}/reset-password"
        )
        return ApiResponse(success=True, message="Password reset email sent")
    except Exception as e:
        logger.error(f"Password reset request failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/password/update",
    response_model=ApiResponse,
    summary="Update password",
    description="Update the password for the authenticated user."
)
async def update_password(
    request: Request,
    body: PasswordUpdateRequest
) -> ApiResponse:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = auth_header.split(" ")[1]
    
    try:
        await auth_service.update_password(token, body.password)
        return ApiResponse(success=True, message="Password updated successfully")
    except Exception as e:
        logger.error(f"Password update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
