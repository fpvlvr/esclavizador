"""
Organization repository for data access.
"""

from typing import Optional

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Repository for organization data access."""

    model = Organization

    async def get_by_name(
        self,
        name: str,
        case_sensitive: bool = False
    ) -> Optional[Organization]:
        """
        Get organization by name.

        Args:
            name: Organization name
            case_sensitive: If True, match exact case (default: False)

        Returns:
            Organization if found, None otherwise
        """
        if case_sensitive:
            return await Organization.filter(name=name).first()
        else:
            # Case-insensitive lookup (iexact in Tortoise ORM)
            return await Organization.filter(name__iexact=name).first()

    async def create_organization(self, name: str) -> Organization:
        """
        Create new organization.

        Args:
            name: Organization name (stored as-is)

        Returns:
            Created organization

        Raises:
            IntegrityError: If organization name already exists
        """
        # Note: Uniqueness check should be done before calling this method
        return await self.create(name=name)


# Singleton instance
organization_repo = OrganizationRepository()
