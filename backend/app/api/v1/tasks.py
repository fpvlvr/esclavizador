"""
Task API routes.

Handles HTTP requests for task CRUD operations.
"""

from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.domain.entities import UserData
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskList
from app.services.task_service import task_service
from app.api.deps import get_current_active_user, require_boss_role


router = APIRouter()


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create new task (boss only)"
)
async def create_task(
    data: TaskCreate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> TaskResponse:
    """Create new task."""
    task_dict = await task_service.create_task(current_user, data)
    return TaskResponse(**task_dict)


@router.get(
    "",
    response_model=TaskList,
    status_code=status.HTTP_200_OK,
    summary="List tasks",
    description="List all tasks in user's organization with optional filtering"
)
async def list_tasks(
    current_user: Annotated[UserData, Depends(get_current_active_user)],
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> TaskList:
    """List tasks with filtering and pagination."""
    result = await task_service.list_tasks(
        user=current_user,
        project_id=str(project_id) if project_id else None,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return TaskList(**result)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task",
    description="Get task by ID"
)
async def get_task(
    task_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TaskResponse:
    """Get task details by ID."""
    task_dict = await task_service.get_task(current_user, str(task_id))
    return TaskResponse(**task_dict)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task",
    description="Update existing task (boss only)"
)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> TaskResponse:
    """Update task."""
    task_dict = await task_service.update_task(
        user=current_user,
        task_id=str(task_id),
        data=data
    )
    return TaskResponse(**task_dict)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Soft delete task (boss only)"
)
async def delete_task(
    task_id: UUID,
    current_user: Annotated[UserData, Depends(require_boss_role)]
):
    """Soft delete task (sets is_active=False)."""
    await task_service.delete_task(current_user, str(task_id))
    return None
