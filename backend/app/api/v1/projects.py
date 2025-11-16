"""
Project API routes.

Handles HTTP requests for project CRUD operations.
"""

from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectList
from app.services.project_service import project_service
from app.api.deps import get_current_active_user, require_master_role


router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="Create new project (master only)"
)
async def create_project(
    data: ProjectCreate,
    current_user: Annotated[User, Depends(require_master_role)]
) -> ProjectResponse:
    """Create new project."""
    project_dict = await project_service.create_project(current_user, data)
    return ProjectResponse(**project_dict)


@router.get(
    "",
    response_model=ProjectList,
    status_code=status.HTTP_200_OK,
    summary="List projects",
    description="List all projects in user's organization with optional filtering"
)
async def list_projects(
    current_user: Annotated[User, Depends(get_current_active_user)],
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> ProjectList:
    """List projects with filtering and pagination."""
    result = await project_service.list_projects(
        user=current_user,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return ProjectList(**result)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project",
    description="Get project by ID"
)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ProjectResponse:
    """Get project details by ID."""
    project_dict = await project_service.get_project(current_user, str(project_id))
    return ProjectResponse(**project_dict)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="Update existing project (master only)"
)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(require_master_role)]
) -> ProjectResponse:
    """Update project."""
    project_dict = await project_service.update_project(
        user=current_user,
        project_id=str(project_id),
        data=data
    )
    return ProjectResponse(**project_dict)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Soft delete project (master only)"
)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(require_master_role)]
):
    """Soft delete project (sets is_active=False)."""
    await project_service.delete_project(current_user, str(project_id))
    return None
