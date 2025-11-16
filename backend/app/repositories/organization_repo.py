"""
Organization repository for data access.

Returns OrganizationData TypedDicts for ORM independence.
"""

from typing import Optional

from app.models.organization import Organization
from app.repositories.base import BaseRepository
from app.domain.entities import OrganizationData


class OrganizationRepository(BaseRepository[Organization, OrganizationData]):
    """Repository for organization data access."""

    model = Organization

    def _to_dict(self, org: Organization) -> OrganizationData:
        """Convert Organization ORM instance to OrganizationData dict."""
        return {
            "id": org.id,
            "name": org.name,
            "created_at": org.created_at,
        }

    async def get_by_name(
        self,
        name: str,
        case_sensitive: bool = False
    ) -> Optional[OrganizationData]:
        """
        Get organization by name.

        Args:
            name: Organization name
            case_sensitive: If True, match exact case (default: False)

        Returns:
            OrganizationData dict if found, None otherwise
        """
        if case_sensitive:
            org = await Organization.filter(name=name).first()
        else:
            # Case-insensitive lookup (iexact in Tortoise ORM)
            org = await Organization.filter(name__iexact=name).first()

        if not org:
            return None

        # Convert ORM → OrganizationData dict using _to_dict
        return self._to_dict(org)

    async def create_organization(self, name: str) -> OrganizationData:
        """
        Create new organization.

        Args:
            name: Organization name (stored as-is)

        Returns:
            Created organization as OrganizationData dict

        Raises:
            IntegrityError: If organization name already exists
        """
        # Note: Uniqueness check should be done before calling this method
        org = await self.create(name=name)

        # Convert ORM → OrganizationData dict using _to_dict
        return self._to_dict(org)


# Singleton instance
organization_repo = OrganizationRepository()
