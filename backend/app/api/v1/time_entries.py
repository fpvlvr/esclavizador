"""
Time entry API routes.

Handles HTTP requests for time tracking operations.
"""

from typing import Annotated, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status

from app.domain.entities import UserData
from app.schemas.time_entry import (
    TimeEntryStart,
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryResponse,
    TimeEntryList
)
from app.services.time_tracking_service import time_tracking_service
from app.api.deps import get_current_active_user


router = APIRouter()


@router.post(
    "/start",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start timer",
    description="Start a new timer for current user"
)
async def start_timer(
    data: TimeEntryStart,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TimeEntryResponse:
    """Start a new timer."""
    entry_dict = await time_tracking_service.start_timer(current_user, data)
    return TimeEntryResponse(**entry_dict)


@router.post(
    "/{entry_id}/stop",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Stop timer",
    description="Stop a running timer (owner only)"
)
async def stop_timer(
    entry_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TimeEntryResponse:
    """Stop a running timer."""
    entry_dict = await time_tracking_service.stop_timer(current_user, str(entry_id))
    return TimeEntryResponse(**entry_dict)


@router.get(
    "/running",
    response_model=Optional[TimeEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get running timer",
    description="Get current user's running timer if any"
)
async def get_running_timer(
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> Optional[TimeEntryResponse]:
    """Get currently running timer for current user."""
    entry_dict = await time_tracking_service.get_running_timer(current_user)
    if entry_dict:
        return TimeEntryResponse(**entry_dict)
    return None


@router.post(
    "",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create manual entry",
    description="Create a manual time entry (already completed)"
)
async def create_manual_entry(
    data: TimeEntryCreate,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TimeEntryResponse:
    """Create a manual time entry."""
    entry_dict = await time_tracking_service.create_manual_entry(current_user, data)
    return TimeEntryResponse(**entry_dict)


@router.get(
    "",
    response_model=TimeEntryList,
    status_code=status.HTTP_200_OK,
    summary="List time entries",
    description="List time entries with optional filtering (workers see own, bosses see all)"
)
async def list_time_entries(
    current_user: Annotated[UserData, Depends(get_current_active_user)],
    project_id: Optional[UUID] = Query(None, description="Filter by project ID"),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    is_billable: Optional[bool] = Query(None, description="Filter by billable status"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID (bosses only)"),
    start_date: Optional[date] = Query(None, description="Filter by start date (entries >= this date)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (entries <= this date)"),
    is_running: Optional[bool] = Query(None, description="Filter by running status"),
    tag_ids: Optional[list[UUID]] = Query(None, description="Filter by tag IDs (OR logic)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> TimeEntryList:
    """List time entries with filtering and pagination."""
    result = await time_tracking_service.list_entries(
        user=current_user,
        project_id=str(project_id) if project_id else None,
        task_id=str(task_id) if task_id else None,
        is_billable=is_billable,
        user_id=str(user_id) if user_id else None,
        start_date=start_date,
        end_date=end_date,
        is_running=is_running,
        tag_ids=[str(tid) for tid in tag_ids] if tag_ids else None,
        limit=limit,
        offset=offset
    )
    return TimeEntryList(**result)


@router.get(
    "/{entry_id}",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get time entry",
    description="Get time entry by ID"
)
async def get_time_entry(
    entry_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TimeEntryResponse:
    """Get time entry details by ID."""
    entry_dict = await time_tracking_service.get_entry(current_user, str(entry_id))
    return TimeEntryResponse(**entry_dict)


@router.put(
    "/{entry_id}",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update time entry",
    description="Update existing time entry"
)
async def update_time_entry(
    entry_id: UUID,
    data: TimeEntryUpdate,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
) -> TimeEntryResponse:
    """Update time entry."""
    entry_dict = await time_tracking_service.update_entry(
        user=current_user,
        entry_id=str(entry_id),
        data=data
    )
    return TimeEntryResponse(**entry_dict)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete time entry",
    description="Hard delete time entry (permanent)"
)
async def delete_time_entry(
    entry_id: UUID,
    current_user: Annotated[UserData, Depends(get_current_active_user)]
):
    """Hard delete time entry (permanent removal)."""
    await time_tracking_service.delete_entry(current_user, str(entry_id))
    return None
