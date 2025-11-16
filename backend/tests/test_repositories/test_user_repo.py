"""
Tests for UserRepository.

Tests user CRUD operations and user-specific queries.
"""

import pytest

from app.repositories.user_repo import user_repo
from app.models.user import UserRole
from app.core.security import hash_password


class TestUserRepository:
    """Test user repository data access."""

    async def test_create_user(self, test_org):
        """Test creating a new user."""
        user = await user_repo.create_user(
            email="newuser@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=test_org["id"]
        )

        assert user is not None
        assert user["id"] is not None
        assert user["email"] == "newuser@example.com"
        assert user["role"] == "slave"
        assert user["organization_id"] == test_org["id"]
        assert user["is_active"] is True
        assert user["created_at"] is not None

        # Cleanup
        await user_repo.delete(user["id"])

    async def test_create_user_master_role(self, test_org):
        """Test creating a user with MASTER role."""
        user = await user_repo.create_user(
            email="master@example.com",
            password_hash=hash_password("MasterPass123!"),
            role=UserRole.MASTER,
            organization_id=test_org["id"]
        )

        assert user["role"] == "master"

        # Cleanup
        await user_repo.delete(user["id"])

    async def test_get_by_id(self, test_org):
        """Test getting user by ID."""
        user = await user_repo.create_user(
            email="idtest@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=test_org["id"]
        )

        # Get by ID
        fetched_user = await user_repo.get_by_id(user["id"])

        assert fetched_user is not None
        assert fetched_user["id"] == user["id"]
        assert fetched_user["email"] == "idtest@example.com"

        # Cleanup
        await user_repo.delete(user["id"])

    async def test_get_by_id_not_found(self):
        """Test getting non-existent user returns None."""
        result = await user_repo.get_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_get_by_email(self, test_org):
        """Test getting user by email address."""
        user = await user_repo.create_user(
            email="email@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=test_org["id"]
        )

        # Get by email
        fetched_user = await user_repo.get_by_email("email@example.com")

        assert fetched_user is not None
        assert fetched_user["id"] == user["id"]
        assert fetched_user["email"] == "email@example.com"

        # Cleanup
        await user_repo.delete(user["id"])

    async def test_get_by_email_not_found(self):
        """Test getting non-existent email returns None."""
        result = await user_repo.get_by_email("nonexistent@example.com")
        assert result is None

    async def test_delete_user(self, test_org):
        """Test deleting user by ID."""
        user = await user_repo.create_user(
            email="delete@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=test_org["id"]
        )

        # Delete
        deleted = await user_repo.delete(user["id"])
        assert deleted is True

        # Verify deletion
        result = await user_repo.get_by_id(user["id"])
        assert result is None

    async def test_delete_nonexistent_user(self):
        """Test deleting non-existent user returns False."""
        deleted = await user_repo.delete("00000000-0000-0000-0000-000000000000")
        assert deleted is False

    async def test_update_user(self, test_org):
        """Test updating user fields."""
        user = await user_repo.create_user(
            email="update@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=test_org["id"]
        )

        # Update user
        updated = await user_repo.update(user["id"], {"is_active": False})

        assert updated is not None
        assert updated["is_active"] is False
        assert updated["email"] == "update@example.com"

        # Cleanup
        await user_repo.delete(user["id"])
