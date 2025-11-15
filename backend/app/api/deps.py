"""
API dependencies for authentication and authorization.

Provides dependency injection functions for:
- Extracting current user from JWT token
- Checking user is active
- Requiring specific roles (master/slave)
"""

from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.repositories.user_repo import user_repo
from app.models.user import User, UserRole


# HTTP Bearer security scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """
    Get current authenticated user from JWT token.

    Extracts Bearer token from Authorization header, decodes it,
    and fetches the user from the database.

    Args:
        credentials: HTTP Bearer credentials (injected by FastAPI)

    Returns:
        Current user

    Raises:
        HTTPException(401): Invalid or expired token, or user not found
    """
    token = credentials.credentials

    try:
        # Decode JWT token
        payload = decode_token(token)

        # Extract user ID from token
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Fetch user from database
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user (checks is_active flag).

    Args:
        current_user: Current user (injected by get_current_user)

    Returns:
        Current active user

    Raises:
        HTTPException(403): Account inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
    return current_user


async def require_master_role(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Require master role for endpoint access.

    Use this dependency on endpoints that should only be
    accessible to master users (admins).

    Args:
        current_user: Current active user (injected by get_current_active_user)

    Returns:
        Current master user

    Raises:
        HTTPException(403): User is not a master
    """
    if current_user.role != UserRole.MASTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master role required"
        )
    return current_user
