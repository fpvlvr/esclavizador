"""
Task service for business logic.

Handles task operations with authorization and multi-tenant enforcement.
Returns domain entity dicts (TaskData) from repository layer.
"""

from typing import Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.domain.entities import TaskData
from app.repositories.task_repo import task_repo
from app.repositories.project_repo import project_repo


class TaskService:
    """Service for task business logic."""

    async def create_task(
        self,
        user: User,
        data: TaskCreate
    ) -> TaskData:
        """
        Create task in project.

        Args:
            user: Authenticated user (master role verified by dependency)
            data: Task creation data

        Returns:
            TaskData dict from repository

        Raises:
            HTTPException(404): Project not found
        """
        org_id = user["organization_id"]

        # Validate project exists and belongs to org (ORM-free validation)
        project_data = await project_repo.get_by_id(str(data.project_id), org_id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Repository handles ORM internally - service stays ORM-free!
        task_data = await task_repo.create(
            name=data.name,
            description=data.description,
            project_id=str(data.project_id)
        )

        return task_data

    async def list_tasks(
        self,
        user: User,
        project_id: Optional[str],
        is_active: Optional[bool],
        limit: int,
        offset: int
    ) -> dict:
        """
        List tasks in user's organization.

        Args:
            user: Authenticated user
            project_id: Optional filter by project
            is_active: Optional filter by active status
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with items (list of TaskData), total, limit, offset

        Raises:
            HTTPException(404): Project filter specified but project not found
        """
        org_id = user["organization_id"]

        # If filtering by project, validate it belongs to org
        if project_id:
            project_data = await project_repo.get_by_id(project_id, org_id)
            if not project_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

        filters = {}
        if project_id:
            filters['project_id'] = project_id
        if is_active is not None:
            filters['is_active'] = is_active

        result = await task_repo.list(org_id, filters, limit, offset)

        # Repository already returns TaskData dicts, just pass through
        return {
            "items": result["items"],
            "total": result["total"],
            "limit": limit,
            "offset": offset
        }

    async def get_task(
        self,
        user: User,
        task_id: str
    ) -> TaskData:
        """
        Get task by ID (within user's org).

        Args:
            user: Authenticated user
            task_id: Task UUID

        Returns:
            TaskData dict from repository

        Raises:
            HTTPException(404): Task not found
        """
        org_id = user["organization_id"]
        task_data = await task_repo.get_by_id(task_id, org_id)

        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        return task_data

    async def update_task(
        self,
        user: User,
        task_id: str,
        data: TaskUpdate
    ) -> TaskData:
        """
        Update task (within user's org).

        Note: Cannot change project_id (not included in TaskUpdate schema)

        Args:
            user: Authenticated user (master role verified by dependency)
            task_id: Task UUID
            data: Update data (only provided fields will be updated)

        Returns:
            Updated TaskData dict from repository

        Raises:
            HTTPException(404): Task not found
        """
        org_id = user["organization_id"]

        update_data = data.model_dump(exclude_unset=True)

        task_data = await task_repo.update(task_id, org_id, update_data)

        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        return task_data

    async def delete_task(
        self,
        user: User,
        task_id: str
    ):
        """
        Soft delete task (within user's org).

        Args:
            user: Authenticated user (master role verified by dependency)
            task_id: Task UUID

        Returns:
            True if deleted

        Raises:
            HTTPException(404): Task not found
        """
        org_id = user["organization_id"]
        deleted = await task_repo.soft_delete(task_id, org_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        return True


# Singleton instance
task_service = TaskService()
