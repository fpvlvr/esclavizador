"""
Tests for UserRepository.

Tests user CRUD operations and user-specific queries.
"""

import pytest

from app.repositories.user_repo import user_repo
from app.repositories.organization_repo import organization_repo
from app.models.user import User, UserRole
from app.core.security import hash_password


class TestUserRepository:
    """Test user repository data access."""

    async def test_create_user(self):
        """Test creating a new user."""
        # Create test organization
        org = await organization_repo.create_organization(name="User Test Org")

        # Create user
        user = await user_repo.create_user(
            email="newuser@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        assert user is not None
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.role == UserRole.SLAVE
        assert user.organization_id == org.id
        assert user.is_active is True
        assert user.created_at is not None

        # Cleanup
        await user.delete()
        await org.delete()

    async def test_create_user_master_role(self):
        """Test creating a user with MASTER role."""
        org = await organization_repo.create_organization(name="Master Test Org")

        user = await user_repo.create_user(
            email="master@example.com",
            password_hash=hash_password("MasterPass123!"),
            role=UserRole.MASTER,
            organization=org
        )

        assert user.role == UserRole.MASTER

        # Cleanup
        await user.delete()
        await org.delete()

    async def test_get_by_id(self):
        """Test getting user by ID."""
        org = await organization_repo.create_organization(name="ID Lookup Org")
        user = await user_repo.create_user(
            email="idtest@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        # Get by ID
        fetched_user = await user_repo.get_by_id(str(user.id))

        assert fetched_user is not None
        assert fetched_user.id == user.id
        assert fetched_user.email == "idtest@example.com"

        # Cleanup
        await user.delete()
        await org.delete()

    async def test_get_by_id_not_found(self):
        """Test getting non-existent user returns None."""
        result = await user_repo.get_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_get_by_email(self):
        """Test getting user by email address."""
        org = await organization_repo.create_organization(name="Email Lookup Org")
        user = await user_repo.create_user(
            email="email@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        # Get by email
        fetched_user = await user_repo.get_by_email("email@example.com")

        assert fetched_user is not None
        assert fetched_user.id == user.id
        assert fetched_user.email == "email@example.com"

        # Cleanup
        await user.delete()
        await org.delete()

    async def test_get_by_email_not_found(self):
        """Test getting non-existent email returns None."""
        result = await user_repo.get_by_email("nonexistent@example.com")
        assert result is None

    async def test_get_by_id_with_org(self):
        """Test getting user with organization prefetched."""
        org = await organization_repo.create_organization(name="Prefetch Org")
        user = await user_repo.create_user(
            email="prefetch@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        # Get with organization prefetched
        fetched_user = await user_repo.get_by_id_with_org(str(user.id))

        assert fetched_user is not None
        assert fetched_user.id == user.id

        # Access organization without additional query (prefetched)
        assert fetched_user.organization.id == org.id
        assert fetched_user.organization.name == "Prefetch Org"

        # Cleanup
        await user.delete()
        await org.delete()

    async def test_get_by_id_with_org_not_found(self):
        """Test getting non-existent user with org returns None."""
        result = await user_repo.get_by_id_with_org("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_delete_user(self):
        """Test deleting user by ID."""
        org = await organization_repo.create_organization(name="Delete User Org")
        user = await user_repo.create_user(
            email="delete@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        # Delete
        deleted = await user_repo.delete(str(user.id))
        assert deleted is True

        # Verify deletion
        result = await user_repo.get_by_id(str(user.id))
        assert result is None

        # Cleanup org
        await org.delete()

    async def test_delete_nonexistent_user(self):
        """Test deleting non-existent user returns False."""
        deleted = await user_repo.delete("00000000-0000-0000-0000-000000000000")
        assert deleted is False

    async def test_user_cascade_delete_with_organization(self):
        """Test that deleting organization cascades to users."""
        org = await organization_repo.create_organization(name="Cascade Org")
        user1 = await user_repo.create_user(
            email="cascade1@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.MASTER,
            organization=org
        )
        user2 = await user_repo.create_user(
            email="cascade2@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization=org
        )

        # Delete organization
        await org.delete()

        # Verify users are also deleted (CASCADE)
        result1 = await user_repo.get_by_id(str(user1.id))
        result2 = await user_repo.get_by_id(str(user2.id))

        assert result1 is None
        assert result2 is None
