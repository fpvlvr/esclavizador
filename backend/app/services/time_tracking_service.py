"""
Time tracking service for business logic.

Handles time entry operations with authorization and multi-tenant enforcement.
Returns domain entity dicts (TimeEntryData) from repository layer.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, date, timezone
from fastapi import HTTPException, status

from app.domain.entities import UserData, TimeEntryData
from app.schemas.time_entry import TimeEntryStart, TimeEntryCreate, TimeEntryUpdate
from app.repositories.time_entry_repo import time_entry_repo
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo
from app.repositories.user_repo import user_repo
from app.repositories.tag_repo import tag_repo


class TimeTrackingService:
    """Service for time tracking business logic."""

    async def start_timer(
        self,
        user: UserData,
        data: TimeEntryStart
    ) -> TimeEntryData:
        """
        Start a new timer for user.

        Args:
            user: Authenticated user
            data: Timer start data

        Returns:
            TimeEntryData dict from repository

        Raises:
            HTTPException(409): User already has a running timer
            HTTPException(404): Project or task not found
        """
        org_id = user["organization_id"]

        # 1. Check for existing running timer
        running = await time_entry_repo.get_running_entry(user["id"], org_id)
        if running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a running timer. Stop it first."
            )

        # 2. Validate project exists and belongs to org
        project = await project_repo.get_by_id(str(data.project_id), str(org_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # 3. If task specified, validate it exists and belongs to project
        if data.task_id:
            task = await task_repo.get_by_id(str(data.task_id), str(org_id))
            if not task or task["project_id"] != data.project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found or doesn't belong to project"
                )

        # 4. Validate tags if provided
        tag_ids = None
        if data.tag_ids:
            tag_ids = [str(tid) for tid in data.tag_ids]
            for tid in tag_ids:
                tag = await tag_repo.get_by_id(tid, str(org_id))
                if not tag:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tag not found: {tid}"
                    )

        # 5. Create timer entry
        return await time_entry_repo.create(
            user_id=str(user["id"]),
            project_id=str(data.project_id),
            task_id=str(data.task_id) if data.task_id else None,
            organization_id=str(org_id),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=data.is_billable,
            description=data.description,
            tag_ids=tag_ids
        )

    async def stop_timer(
        self,
        user: UserData,
        entry_id: str
    ) -> TimeEntryData:
        """
        Stop user's running timer.

        Args:
            user: Authenticated user
            entry_id: TimeEntry UUID

        Returns:
            Updated TimeEntryData dict from repository

        Raises:
            HTTPException(404): Time entry not found
            HTTPException(403): Not the owner of the timer
            HTTPException(400): Timer already stopped
        """
        org_id = user["organization_id"]

        # 1. Get entry
        entry = await time_entry_repo.get_by_id(entry_id, str(org_id))
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        # 2. Authorization: must be owner (even bosses can only stop their own timers)
        if entry["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only stop your own timers"
            )

        # 3. Check if already stopped
        if not entry["is_running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timer is already stopped"
            )

        # 4. Stop it
        return await time_entry_repo.stop_timer(entry_id, datetime.now(timezone.utc))

    async def get_running_timer(
        self,
        user: UserData
    ) -> Optional[TimeEntryData]:
        """
        Get user's currently running timer.

        Args:
            user: Authenticated user

        Returns:
            TimeEntryData dict if running timer exists, else None
        """
        return await time_entry_repo.get_running_entry(user["id"], user["organization_id"])

    async def create_manual_entry(
        self,
        user: UserData,
        data: TimeEntryCreate
    ) -> TimeEntryData:
        """
        Create a manual time entry (already completed).

        Args:
            user: Authenticated user
            data: Time entry creation data

        Returns:
            TimeEntryData dict from repository

        Raises:
            HTTPException(400): Invalid times or overlap detected
            HTTPException(404): Project or task not found
        """
        org_id = user["organization_id"]

        # 1. Validate times (additional check, Pydantic already validates)
        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time"
            )

        if data.start_time > datetime.now(timezone.utc) or data.end_time > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Times cannot be in the future"
            )

        # 2. Check for overlapping entries
        has_overlap = await time_entry_repo.check_overlap(
            user_id=str(user["id"]),
            start_time=data.start_time,
            end_time=data.end_time
        )
        if has_overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time entry overlaps with existing entry or running timer"
            )

        # 3. Validate project exists and belongs to org
        project = await project_repo.get_by_id(str(data.project_id), str(org_id))
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # 4. If task specified, validate it exists and belongs to project
        if data.task_id:
            task = await task_repo.get_by_id(str(data.task_id), str(org_id))
            if not task or task["project_id"] != data.project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found or doesn't belong to project"
                )

        # 5. Validate tags if provided
        tag_ids = None
        if data.tag_ids:
            tag_ids = [str(tid) for tid in data.tag_ids]
            for tid in tag_ids:
                tag = await tag_repo.get_by_id(tid, str(org_id))
                if not tag:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Tag not found: {tid}"
                    )

        # 6. Create entry (not running, has end_time)
        return await time_entry_repo.create(
            user_id=str(user["id"]),
            project_id=str(data.project_id),
            task_id=str(data.task_id) if data.task_id else None,
            organization_id=str(org_id),
            start_time=data.start_time,
            end_time=data.end_time,
            is_running=False,
            is_billable=data.is_billable,
            description=data.description,
            tag_ids=tag_ids
        )

    async def list_entries(
        self,
        user: UserData,
        project_id: Optional[str],
        task_id: Optional[str],
        is_billable: Optional[bool],
        user_id: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
        is_running: Optional[bool],
        tag_ids: Optional[list[str]],
        limit: int,
        offset: int
    ) -> dict:
        """
        List time entries in user's organization.

        Args:
            user: Authenticated user
            project_id: Optional filter by project
            task_id: Optional filter by task
            is_billable: Optional filter by billable status
            user_id: Optional filter by user (bosses only)
            start_date: Optional filter by start date (>=)
            end_date: Optional filter by end date (<=)
            is_running: Optional filter by running status
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with items (list of TimeEntryData), total, limit, offset

        Raises:
            HTTPException(403): Worker trying to filter by user_id
            HTTPException(404): User filter specified but user not found
        """
        org_id = user["organization_id"]
        filters = {}

        # Authorization: workers can only see their own entries
        if user["role"] == "worker":
            filters["user_id"] = str(user["id"])

            # Workers cannot filter by other users
            if user_id and user_id != str(user["id"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own time entries"
                )
        else:
            # Bosses can filter by user_id
            if user_id:
                # Validate user exists and belongs to same org
                filter_user = await user_repo.get_by_id(user_id)
                if not filter_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                if filter_user["organization_id"] != org_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                filters["user_id"] = user_id

        # Add other filters
        if project_id:
            filters["project_id"] = project_id
        if task_id:
            filters["task_id"] = task_id
        if is_billable is not None:
            filters["is_billable"] = is_billable
        if is_running is not None:
            filters["is_running"] = is_running
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if tag_ids:
            filters["tag_ids"] = tag_ids

        result = await time_entry_repo.list(str(org_id), filters, limit, offset)

        return {
            "items": result["items"],
            "total": result["total"],
            "limit": limit,
            "offset": offset
        }

    async def get_entry(
        self,
        user: UserData,
        entry_id: str
    ) -> TimeEntryData:
        """
        Get time entry by ID (within user's org).

        Args:
            user: Authenticated user
            entry_id: TimeEntry UUID

        Returns:
            TimeEntryData dict from repository

        Raises:
            HTTPException(404): Entry not found
            HTTPException(403): Worker trying to view another user's entry
        """
        org_id = user["organization_id"]
        entry = await time_entry_repo.get_by_id(entry_id, str(org_id))

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        # Authorization: workers can only see their own entries
        if user["role"] == "worker" and entry["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own time entries"
            )

        return entry

    async def update_entry(
        self,
        user: UserData,
        entry_id: str,
        data: TimeEntryUpdate
    ) -> TimeEntryData:
        """
        Update time entry (within user's org).

        Args:
            user: Authenticated user
            entry_id: TimeEntry UUID
            data: Update data (only provided fields will be updated)

        Returns:
            Updated TimeEntryData dict from repository

        Raises:
            HTTPException(404): Entry not found or project/task invalid
            HTTPException(403): Worker trying to edit another user's entry
            HTTPException(400): Invalid update (running timer times, overlaps, etc.)
        """
        org_id = user["organization_id"]

        # 1. Get entry
        entry = await time_entry_repo.get_by_id(entry_id, str(org_id))
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        # 2. Authorization: owner or boss
        if user["role"] == "worker" and entry["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own time entries"
            )

        # 3. Build update dict
        update_dict = data.model_dump(exclude_unset=True)

        # 4. Cannot update running timer's times
        if entry["is_running"] and ('start_time' in update_dict or 'end_time' in update_dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update times of running timer. Stop it first."
            )

        # 5. Validate time consistency
        new_start = update_dict.get('start_time', entry['start_time'])
        new_end = update_dict.get('end_time', entry['end_time'])

        if new_end and new_start >= new_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be before end_time"
            )

        # 6. Check for overlaps if times are being updated
        if 'start_time' in update_dict or 'end_time' in update_dict:
            if new_end:  # Only check if entry will have an end_time
                has_overlap = await time_entry_repo.check_overlap(
                    user_id=str(entry["user_id"]),
                    start_time=new_start,
                    end_time=new_end,
                    exclude_entry_id=entry_id
                )
                if has_overlap:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Updated times overlap with existing entry or running timer"
                    )

        # 7. Validate project if being updated
        if 'project_id' in update_dict:
            project = await project_repo.get_by_id(str(update_dict['project_id']), str(org_id))
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

        # 8. Validate task if being updated
        if 'task_id' in update_dict and update_dict['task_id']:
            project_id = update_dict.get('project_id', entry['project_id'])
            task = await task_repo.get_by_id(str(update_dict['task_id']), str(org_id))
            if not task or task["project_id"] != project_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found or doesn't belong to project"
                )

        # 9. Validate tags if being updated
        if 'tag_ids' in update_dict:
            tag_ids = update_dict['tag_ids']
            if tag_ids:  # If not empty list
                tag_ids_str = [str(tid) for tid in tag_ids]
                for tid in tag_ids_str:
                    tag = await tag_repo.get_by_id(tid, str(org_id))
                    if not tag:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Tag not found: {tid}"
                        )
                update_dict['tag_ids'] = tag_ids_str
            # else: empty list means remove all tags

        # 10. Update
        updated = await time_entry_repo.update(entry_id, org_id, update_dict)

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        return updated

    async def delete_entry(
        self,
        user: UserData,
        entry_id: str
    ):
        """
        Hard delete time entry (within user's org).

        Args:
            user: Authenticated user
            entry_id: TimeEntry UUID

        Returns:
            True if deleted

        Raises:
            HTTPException(404): Entry not found
            HTTPException(403): Worker trying to delete another user's entry
        """
        org_id = user["organization_id"]

        # Get entry first for authorization check
        entry = await time_entry_repo.get_by_id(entry_id, str(org_id))
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        # Authorization: owner or boss
        if user["role"] == "worker" and entry["user_id"] != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own time entries"
            )

        deleted = await time_entry_repo.delete(entry_id, org_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time entry not found"
            )

        return True


# Singleton instance
time_tracking_service = TimeTrackingService()
