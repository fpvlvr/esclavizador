"""User service for business logic."""

from typing import Optional
from datetime import date
from fastapi import HTTPException, status

from app.domain.entities import UserData
from app.schemas.user import UserUpdate, UserCreate
from app.repositories.user_repo import user_repo
from app.core.security import hash_password


class UserService:
    """Service for user management business logic."""

    async def list_users(
        self,
        current_user: UserData,
        is_active: Optional[bool],
        role: Optional[str],
        limit: int,
        offset: int
    ) -> dict:
        """Multi-tenant list - only users in current user's org."""
        org_id = current_user["organization_id"]

        filters = {}
        if is_active is not None:
            filters['is_active'] = is_active
        if role is not None:
            filters['role'] = role

        result = await user_repo.list(org_id, filters, limit, offset)
        return result

    async def get_user(
        self,
        current_user: UserData,
        user_id: str
    ) -> UserData:
        """
        Get user by ID with org enforcement.

        Raises 404 if not found or wrong org (security: don't reveal existence).
        """
        user = await user_repo.get_by_id(user_id)

        if not user or user["organization_id"] != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    async def update_user(
        self,
        current_user: UserData,
        user_id: str,
        data: UserUpdate
    ) -> UserData:
        """
        Update user role/status.

        Edge case: Boss cannot deactivate themselves (would lock out of system).
        """
        # Verify user exists and is in same org
        user = await self.get_user(current_user, user_id)

        # Prevent boss from deactivating themselves
        if user["id"] == current_user["id"] and data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        # Build update dict (only non-None fields)
        update_data = {}
        if data.role is not None:
            update_data['role'] = data.role
        if data.is_active is not None:
            update_data['is_active'] = data.is_active

        if not update_data:
            # No fields to update - return current user
            return user

        updated_user = await user_repo.update(user_id, update_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return updated_user

    async def create_user(
        self,
        current_user: UserData,
        data: UserCreate
    ) -> UserData:
        """
        Create user in current user's organization.

        Edge case: Email uniqueness is global across all organizations.
        """
        # Check if email already exists
        existing_user = await user_repo.get_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Hash password
        hashed_pwd = hash_password(data.password)

        # Create user in current user's organization
        org_id = current_user["organization_id"]

        user_data = await user_repo.create_user(
            email=data.email,
            password_hash=hashed_pwd,
            role=data.role,
            organization_id=str(org_id)
        )

        return user_data

    async def delete_user(
        self,
        current_user: UserData,
        user_id: str
    ) -> None:
        """
        Delete user (hard delete, cascades to time entries).

        Edge cases:
        - Cannot delete yourself (would lock out)
        - Can only delete users in your organization
        """
        # Verify user exists and is in same org
        user = await self.get_user(current_user, user_id)

        # Prevent self-deletion
        if user["id"] == current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Hard delete (cascades to TimeEntry, RefreshToken)
        deleted = await user_repo.delete(user_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    async def list_user_stats(
        self,
        current_user: UserData,
        start_date: Optional[date],
        end_date: Optional[date],
        is_active: Optional[bool],
        role: Optional[str],
        limit: int,
        offset: int
    ) -> dict:
        """
        Multi-tenant list with stats (projects + time for date range).

        Returns users with total_time_seconds and projects list.
        """
        org_id = current_user["organization_id"]

        filters = {}
        if is_active is not None:
            filters['is_active'] = is_active
        if role is not None:
            filters['role'] = role

        result = await user_repo.list_stats(
            org_id=org_id,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            limit=limit,
            offset=offset
        )
        return result


# Singleton instance
user_service = UserService()
