"""
Reports API routes.

Handles HTTP requests for analytics and reporting operations.
"""

from typing import Annotated, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, Query, status

from app.domain.entities import UserData
from app.schemas.time_entry import ProjectAggregateList
from app.services.time_tracking_service import time_tracking_service
from app.api.deps import require_boss_role


router = APIRouter()


@router.get(
    "/projects",
    response_model=ProjectAggregateList,
    status_code=status.HTTP_200_OK,
    summary="Get project aggregates",
    description="Get time entries aggregated by project for reports (boss only)"
)
async def get_project_aggregates(
    current_user: Annotated[UserData, Depends(require_boss_role)],
    start_date: Optional[date] = Query(None, description="Filter by start date (entries >= this date)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (entries <= this date)"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID")
) -> ProjectAggregateList:
    """Get time entries aggregated by project for reports."""
    aggregates = await time_tracking_service.get_project_aggregates(
        user=current_user,
        start_date=start_date,
        end_date=end_date,
        user_id=str(user_id) if user_id else None
    )
    return ProjectAggregateList(items=aggregates)

