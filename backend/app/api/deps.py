"""
API dependencies for authentication and authorization.

Provides dependency injection functions for:
- Extracting current user from JWT token
- Checking user is active
- Requiring specific roles (boss/worker)

ORM-free dependencies - work with UserData TypedDicts.
"""

from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.repositories.user_repo import user_repo
from app.domain.entities import UserData


# HTTP Bearer security scheme for extracting JWT from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> UserData:
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

        # Fetch user from database (returns UserData dict)
        user_data = await user_repo.get_by_id(user_id)
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_data

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
    current_user: Annotated[UserData, Depends(get_current_user)]
) -> UserData:
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
    return current_user


async def require_boss_role(
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> UserData:
    if current_user["role"] != "boss":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Boss role required"
        )
    return current_user
