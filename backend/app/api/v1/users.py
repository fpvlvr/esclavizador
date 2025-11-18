"""User management API routes (boss only)."""

from typing import Annotated, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status

from app.domain.entities import UserData
from app.schemas.user import UserUpdate, UserResponse, UserList, UserCreate, UserStatsList
from app.services.user_service import user_service
from app.api.deps import require_boss_role


router = APIRouter()


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create new user in organization (boss only)"
)
async def create_user(
    data: UserCreate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> UserResponse:
    user_dict = await user_service.create_user(current_user, data)
    return UserResponse(**user_dict)


@router.get(
    "",
    response_model=UserList,
    status_code=status.HTTP_200_OK,
    summary="List users",
    description="List all users in organization (boss only)"
)
async def list_users(
    current_user: Annotated[UserData, Depends(require_boss_role)],
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role (boss/worker)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> UserList:
    result = await user_service.list_users(
        current_user=current_user,
        is_active=is_active,
        role=role,
        limit=limit,
        offset=offset
    )
    return UserList(**result)


@router.get(
    "/stats",
    response_model=UserStatsList,
    status_code=status.HTTP_200_OK,
    summary="List users with stats",
    description="List users with aggregated stats: projects and total time for date range (boss only)"
)
async def list_user_stats(
    current_user: Annotated[UserData, Depends(require_boss_role)],
    start_date: Optional[date] = Query(None, description="Filter time entries from this date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter time entries until this date (exclusive)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role (boss/worker)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> UserStatsList:
    result = await user_service.list_user_stats(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
        role=role,
        limit=limit,
        offset=offset
    )
    return UserStatsList(**result)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user",
    description="Get user by ID (boss only)"
)
async def get_user(
    user_id: UUID,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> UserResponse:
    user_dict = await user_service.get_user(current_user, str(user_id))
    return UserResponse(**user_dict)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update user role/status (boss only)"
)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> UserResponse:
    user_dict = await user_service.update_user(current_user, str(user_id), data)
    return UserResponse(**user_dict)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete user (boss only, hard delete)"
)
async def delete_user(
    user_id: UUID,
    current_user: Annotated[UserData, Depends(require_boss_role)]
) -> None:
    await user_service.delete_user(current_user, str(user_id))
