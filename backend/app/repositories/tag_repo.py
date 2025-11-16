"""
Tag repository for database operations.

Handles all database queries for Tag model with multi-tenant isolation.
Returns TypedDict entities for ORM independence.
"""

from typing import Optional
from uuid import UUID
from tortoise.exceptions import IntegrityError

from app.models.tag import Tag
from app.repositories.base import BaseRepository
from app.domain.entities import TagData


class TagRepository(BaseRepository[Tag, TagData]):
    """Repository for tag data access."""

    model = Tag

    def _to_dict(self, tag: Tag) -> TagData:
        """Convert Tag ORM instance to TagData dict."""
        return {
            "id": tag.id,
            "name": tag.name,
            "organization_id": tag.organization_id,
            "created_at": tag.created_at,
        }

    async def create(
        self,
        name: str,
        org_id: str
    ) -> TagData:
        """
        Create new tag in organization.

        Args:
            name: Tag name (unique per organization)
            org_id: Organization UUID

        Returns:
            Tag data dict

        Raises:
            IntegrityError: If tag with same name exists in organization
        """
        tag = await self.model.create(
            name=name,
            organization_id=org_id
        )

        return self._to_dict(tag)

    async def get_by_id(
        self,
        tag_id: str,
        org_id: str
    ) -> Optional[TagData]:
        """
        Get tag by ID with multi-tenant filtering.

        Args:
            tag_id: Tag UUID
            org_id: Organization UUID

        Returns:
            Tag data dict, or None if not found or wrong org
        """
        tag = await self.model.filter(
            id=tag_id,
            organization_id=org_id
        ).first()

        if not tag:
            return None

        return self._to_dict(tag)

    async def get_by_name(
        self,
        name: str,
        org_id: str
    ) -> Optional[TagData]:
        """
        Get tag by name (case-insensitive) in organization.

        Args:
            name: Tag name
            org_id: Organization UUID

        Returns:
            Tag data dict, or None if not found
        """
        tag = await self.model.filter(
            name__iexact=name,  # Case-insensitive
            organization_id=org_id
        ).first()

        if not tag:
            return None

        return self._to_dict(tag)

    async def list(
        self,
        org_id: UUID | str,
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """
        List tags with filtering and pagination.

        Args:
            org_id: Organization UUID
            filters: Dict with optional keys (currently none supported)
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with keys: items (list of TagData dicts), total (int)
        """
        # Base query with org filter
        query = self.model.filter(organization_id=org_id)

        # Get total count
        total = await query.count()

        # Get paginated results
        tags = await query.offset(offset).limit(limit).all()

        # Convert ORM objects → TagData dicts
        items = [self._to_dict(t) for t in tags]

        return {
            "items": items,
            "total": total
        }

    async def update(
        self,
        tag_id: str,
        org_id: UUID | str,
        data: dict
    ) -> Optional[TagData]:
        """
        Update tag with multi-tenant filtering.

        Args:
            tag_id: Tag UUID
            org_id: Organization UUID
            data: Dict of fields to update (name)

        Returns:
            Updated tag data dict, or None if not found

        Raises:
            IntegrityError: If updated name conflicts with existing tag
        """
        tag = await self.model.filter(
            id=tag_id,
            organization_id=org_id
        ).first()

        if not tag:
            return None

        # Update fields
        for key, value in data.items():
            setattr(tag, key, value)

        await tag.save()

        return self._to_dict(tag)

    async def delete(
        self,
        tag_id: str,
        org_id: str
    ) -> bool:
        """
        Hard delete tag (cascade removes from time_entry_tags junction table).

        Args:
            tag_id: Tag UUID
            org_id: Organization UUID

        Returns:
            True if deleted, False if not found
        """
        tag = await self.model.filter(
            id=tag_id,
            organization_id=org_id
        ).first()

        if not tag:
            return False

        await tag.delete()

        return True


# Singleton instance
tag_repo = TagRepository()
