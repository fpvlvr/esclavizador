"""Tag API routes."""

from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.domain.entities import UserData
from app.schemas.tag import TagCreate, TagUpdate, TagResponse, TagList
from app.services.tag_service import tag_service
from app.api.deps import get_current_active_user, require_boss_role


router = APIRouter()


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tag",
    description="Create new tag (boss only)"
)
async def create_tag(
    data: TagCreate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> TagResponse:
    """Create new tag."""
    tag_dict = await tag_service.create_tag(current_user, data)
    return TagResponse(**tag_dict)


@router.get(
    "",
    response_model=TagList,
    status_code=status.HTTP_200_OK,
    summary="List tags",
    description="List all tags in user's organization"
)
async def list_tags(
    current_user: Annotated[UserData, Depends(get_current_active_user)],
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> TagList:
    """List tags with pagination."""
    result = await tag_service.list_tags(
        user=current_user,
        limit=limit,
        offset=offset
    )
    return TagList(**result)


@router.get(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Get tag",
    description="Get tag by ID"
)
async def get_tag(
    tag_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TagResponse:
    """Get tag details by ID."""
    tag_dict = await tag_service.get_tag(current_user, str(tag_id))
    return TagResponse(**tag_dict)


@router.put(
    "/{tag_id}",
    response_model=TagResponse,
    status_code=status.HTTP_200_OK,
    summary="Update tag",
    description="Update existing tag (boss only)"
)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> TagResponse:
    """Update tag."""
    tag_dict = await tag_service.update_tag(
        user=current_user,
        tag_id=str(tag_id),
        data=data
    )
    return TagResponse(**tag_dict)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Hard delete tag (boss only, cascade removes from time entries)"
)
async def delete_tag(
    tag_id: UUID,
    current_user: Annotated[UserData, Depends(require_boss_role)]
):
    """Hard delete tag (cascade removes from time entries)."""
    await tag_service.delete_tag(current_user, str(tag_id))
    return None
