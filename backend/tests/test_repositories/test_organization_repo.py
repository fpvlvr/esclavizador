"""
Tests for OrganizationRepository.

Tests CRUD operations and organization-specific queries.
"""

import pytest
from tortoise.exceptions import IntegrityError

from app.repositories.organization_repo import organization_repo
from app.models.organization import Organization


class TestOrganizationRepository:
    """Test organization repository data access."""

    async def test_create_organization(self):
        """Test creating a new organization."""
        org = await organization_repo.create_organization(name="New Test Org")

        assert org is not None
        assert org.id is not None
        assert org.name == "New Test Org"
        assert org.created_at is not None

        # Cleanup
        await org.delete()

    async def test_create_duplicate_organization_name(self):
        """Test that duplicate org names raise IntegrityError."""
        await organization_repo.create_organization(name="Duplicate Org")

        # Attempting to create another org with the same name should fail
        with pytest.raises(IntegrityError):
            await organization_repo.create_organization(name="Duplicate Org")

        # Cleanup
        org = await Organization.filter(name="Duplicate Org").first()
        if org:
            await org.delete()

    async def test_get_by_id(self):
        """Test getting organization by ID."""
        org = await organization_repo.create_organization(name="ID Test Org")

        # Get by ID
        fetched_org = await organization_repo.get_by_id(str(org.id))

        assert fetched_org is not None
        assert fetched_org.id == org.id
        assert fetched_org.name == "ID Test Org"

        # Cleanup
        await org.delete()

    async def test_get_by_id_not_found(self):
        """Test getting non-existent organization returns None."""
        result = await organization_repo.get_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    async def test_get_by_name_case_sensitive(self):
        """Test getting organization by name (case-sensitive)."""
        org = await organization_repo.create_organization(name="CaseSensitive")

        # Exact match should work
        result = await organization_repo.get_by_name("CaseSensitive", case_sensitive=True)
        assert result is not None
        assert result.id == org.id

        # Different case should NOT work
        result = await organization_repo.get_by_name("casesensitive", case_sensitive=True)
        assert result is None

        # Cleanup
        await org.delete()

    async def test_get_by_name_case_insensitive(self):
        """Test getting organization by name (case-insensitive, default)."""
        org = await organization_repo.create_organization(name="MixedCase")

        # All case variations should work
        result1 = await organization_repo.get_by_name("MixedCase", case_sensitive=False)
        result2 = await organization_repo.get_by_name("mixedcase", case_sensitive=False)
        result3 = await organization_repo.get_by_name("MIXEDCASE", case_sensitive=False)

        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1.id == org.id
        assert result2.id == org.id
        assert result3.id == org.id

        # Cleanup
        await org.delete()

    async def test_get_by_name_not_found(self):
        """Test getting non-existent organization returns None."""
        result = await organization_repo.get_by_name("NonExistent")
        assert result is None

    async def test_delete_organization(self):
        """Test deleting organization by ID."""
        org = await organization_repo.create_organization(name="Delete Test")

        # Delete
        deleted = await organization_repo.delete(str(org.id))
        assert deleted is True

        # Verify deletion
        result = await organization_repo.get_by_id(str(org.id))
        assert result is None

    async def test_delete_nonexistent_organization(self):
        """Test deleting non-existent organization returns False."""
        deleted = await organization_repo.delete("00000000-0000-0000-0000-000000000000")
        assert deleted is False
