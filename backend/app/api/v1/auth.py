"""
Authentication API endpoints.

Endpoints:
- POST /auth/register - Register new user
- POST /auth/login - Login and get tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout (revoke refresh token)
- GET /auth/me - Get current user info
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshResponse
)
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service
from app.api.deps import get_current_active_user
from app.domain.entities import UserData
from app.core.config import settings


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create new user account and organization. Organization name must be unique.",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "Email or organization name already exists"},
        422: {"description": "Validation error (weak password, invalid email, etc.)"}
    }
)
async def register(request: RegisterRequest) -> UserResponse:
    """
    Register new user and create organization.

    - Email must be unique
    - Organization name must be unique (case-insensitive)
    - Password must meet security requirements (8+ chars, mixed case, digit, special char)
    - Returns created user details (without password)
    """
    user_dict = await auth_service.register(
        email=request.email,
        password=request.password,
        role=request.role,
        organization_name=request.organization_name
    )

    return UserResponse(**user_dict)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user and receive JWT tokens (access + refresh)",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        403: {"description": "Inactive account"}
    }
)
async def login(request: LoginRequest) -> TokenResponse:
    """
    Login and receive JWT tokens.

    - Returns access token (30 min expiry) and refresh token (7 days expiry)
    - Access token used for API requests
    - Refresh token used to get new access tokens
    """
    user, access_token, refresh_token = await auth_service.authenticate(
        email=request.email,
        password=request.password
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get new access token using refresh token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"}
    }
)
async def refresh(request: RefreshRequest) -> RefreshResponse:
    """
    Refresh access token.

    - Provide refresh token to get new access token
    - Refresh token must be valid (not expired, not revoked)
    - Returns new access token (30 min expiry)
    """
    access_token = await auth_service.refresh_access_token(request.refresh_token)

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Revoke refresh token (invalidate session)",
    responses={
        204: {"description": "Logout successful"},
        401: {"description": "Invalid refresh token"}
    }
)
async def logout(request: RefreshRequest):
    """
    Logout and revoke refresh token.

    - Revokes the provided refresh token
    - After logout, the refresh token cannot be used
    - Access token remains valid until expiry (30 min)
    """
    await auth_service.logout(request.refresh_token)
    return None  # 204 No Content


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get authenticated user information",
    responses={
        200: {"description": "User info retrieved successfully"},
        401: {"description": "Invalid or expired token"},
        403: {"description": "Inactive account"}
    }
)
async def get_me(
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> UserResponse:
    """
    Get current authenticated user info.

    - Requires valid access token in Authorization header
    - Returns user details (email, role, organization, etc.)
    - Useful for frontend to verify token and display user info
    """
    return UserResponse(**current_user)
