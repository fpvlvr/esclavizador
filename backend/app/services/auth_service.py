"""
Authentication service with business logic.

Handles:
- User registration with organization creation
- User authentication (login)
- JWT token generation and refresh
- Logout (token revocation)

ORM-free service - works with TypedDict entities only.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple
import jwt
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

logger = logging.getLogger(__name__)

from app.domain.constants import UserRole
from app.domain.entities import UserData
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.core.config import settings
from app.repositories.user_repo import user_repo
from app.repositories.organization_repo import organization_repo
from app.repositories.refresh_token_repo import refresh_token_repo


class AuthService:
    """Authentication service for user management and token operations."""

    async def register(
        self,
        email: str,
        password: str,
        role: UserRole,
        organization_name: str
    ) -> UserData:
        """
        Register new user with new organization.

        Flow:
        1. Check if email already exists → 409 if yes
        2. Check if organization exists (case-insensitive) → 409 if yes
        3. Create new organization (always new)
        4. Hash password
        5. Create user linked to new organization
        6. Return user data dict

        Args:
            email: User email
            password: Plain text password
            role: User role (BOSS or WORKER)
            organization_name: Organization name

        Returns:
            Created user as UserData dict

        Raises:
            HTTPException(409): Email already registered OR organization name already exists
            HTTPException(400): Organization/user creation failed
        """
        # Check if email already exists
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Check if organization name exists (case-insensitive)
        existing_org = await organization_repo.get_by_name(organization_name)
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization name already exists. Please choose a different name or contact your organization administrator to be invited."
            )

        # Hash password before transaction
        hashed_pwd = hash_password(password)

        # Create organization and user in transaction
        try:
            async with in_transaction():
                # Create new organization (returns OrganizationData dict)
                org_data = await organization_repo.create_organization(name=organization_name)

                # Create user (returns UserData dict)
                user_data = await user_repo.create_user(
                    email=email,
                    password_hash=hashed_pwd,
                    role=role,
                    organization_id=str(org_data["id"])  # Pass ID, not ORM object
                )

                return user_data

        except Exception as e:
            logger.error(
                f"Failed to create user and organization: {str(e)}",
                exc_info=e,
                extra={
                    "email": email,
                    "organization_name": organization_name,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user and organization: {str(e)}"
            )

    async def authenticate(
        self,
        email: str,
        password: str
    ) -> Tuple[UserData, str, str]:
        """
        Authenticate user and generate tokens.

        Flow:
        1. Get user by email
        2. Verify password
        3. Check is_active
        4. Generate access token
        5. Generate refresh token
        6. Store refresh token in DB
        7. Return (user_data, access_token, refresh_token)

        Args:
            email: User email
            password: Plain text password

        Returns:
            (UserData dict, access_token, refresh_token)

        Raises:
            HTTPException(401): Invalid credentials
            HTTPException(403): Inactive account
        """
        # Get user by email (returns UserData dict)
        user_data = await user_repo.get_by_email(email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password
        if not verify_password(password, user_data["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive account"
            )

        # Generate access token
        access_token = create_access_token(
            user_id=str(user_data["id"]),
            email=user_data["email"],
            role=user_data["role"],
            org_id=str(user_data["organization_id"])
        )

        # Generate refresh token
        refresh_token, jti = create_refresh_token(user_id=str(user_data["id"]))

        # Store refresh token in database (hashed)
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        await refresh_token_repo.create_token(
            user_id=str(user_data["id"]),  # Pass ID, not ORM object
            token_hash=token_hash,
            expires_at=expires_at
        )

        return user_data, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Flow:
        1. Decode refresh token
        2. Hash token and check DB
        3. Verify not revoked and not expired
        4. Get user from token
        5. Generate new access token
        6. Return new access token

        Args:
            refresh_token: Refresh token string

        Returns:
            New access token

        Raises:
            HTTPException(401): Invalid or expired refresh token
        """
        try:
            # Decode refresh token
            payload = decode_token(refresh_token)

            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Hash token and check in database (returns RefreshTokenData dict)
            token_hash = hash_token(refresh_token)
            db_token = await refresh_token_repo.get_by_hash(token_hash)

            if not db_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )

            # Get user (returns UserData dict)
            user_id = payload.get("sub")
            user_data = await user_repo.get_by_id(user_id)

            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Check if user is active
            if not user_data["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive account"
                )

            # Generate new access token
            access_token = create_access_token(
                user_id=str(user_data["id"]),
                email=user_data["email"],
                role=user_data["role"],
                org_id=str(user_data["organization_id"])
            )

            return access_token

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def logout(self, refresh_token: str) -> bool:
        """
        Revoke refresh token (logout).

        Flow:
        1. Decode refresh token
        2. Hash token
        3. Mark as revoked in DB
        4. Return success

        Args:
            refresh_token: Refresh token string

        Returns:
            True if revoked successfully

        Raises:
            HTTPException(401): Invalid refresh token
        """
        try:
            # Decode token to validate it
            payload = decode_token(refresh_token)

            # Verify it's a refresh token
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Hash token and revoke in database
            token_hash = hash_token(refresh_token)
            revoked = await refresh_token_repo.revoke_token(token_hash)

            if not revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            return True

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )


# Singleton instance
auth_service = AuthService()
