"""Tag service for business logic."""

from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError

from app.domain.entities import UserData, TagData
from app.schemas.tag import TagCreate, TagUpdate
from app.repositories.tag_repo import tag_repo


class TagService:
    """Service for tag business logic."""

    async def create_tag(
        self,
        user: UserData,
        data: TagCreate
    ) -> TagData:
        """
        Raises HTTPException(409) if tag name already exists in organization.
        """
        org_id = str(user["organization_id"])

        # Validate name (strip whitespace)
        name = data.name.strip()
        if not name or len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag name must be 1-100 characters"
            )

        # Check for duplicate (case-insensitive)
        existing = await tag_repo.get_by_name(name, org_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{name}' already exists in organization"
            )

        try:
            tag_data = await tag_repo.create(name=name, org_id=org_id)
            return tag_data
        except IntegrityError:
            # Race condition: tag created between check and create
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{name}' already exists in organization"
            )

    async def list_tags(
        self,
        user: UserData,
        limit: int,
        offset: int
    ) -> dict:
        org_id = user["organization_id"]
        filters = {}
        result = await tag_repo.list(org_id, filters, limit, offset)

        return {
            "items": result["items"],
            "total": result["total"],
            "limit": limit,
            "offset": offset
        }

    async def get_tag(
        self,
        user: UserData,
        tag_id: str
    ) -> TagData:
        org_id = str(user["organization_id"])
        tag_data = await tag_repo.get_by_id(tag_id, org_id)

        if not tag_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        return tag_data

    async def update_tag(
        self,
        user: UserData,
        tag_id: str,
        data: TagUpdate
    ) -> TagData:
        org_id = str(user["organization_id"])

        # Validate tag exists
        existing_tag = await tag_repo.get_by_id(tag_id, org_id)
        if not existing_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        # Validate new name
        name = data.name.strip()
        if not name or len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag name must be 1-100 characters"
            )

        # Check for duplicate (excluding self, case-insensitive)
        duplicate = await tag_repo.get_by_name(name, org_id)
        if duplicate and str(duplicate["id"]) != tag_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{name}' already exists in organization"
            )

        try:
            tag_data = await tag_repo.update(tag_id, org_id, {"name": name})
            if not tag_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tag not found"
                )
            return tag_data
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{name}' already exists in organization"
            )

    async def delete_tag(
        self,
        user: UserData,
        tag_id: str
    ):
        org_id = str(user["organization_id"])
        deleted = await tag_repo.delete(tag_id, org_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        return True


# Singleton instance
tag_service = TagService()
