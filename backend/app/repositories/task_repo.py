"""
Task repository for database operations.

Handles all database queries for Task model with multi-tenant isolation via project.
Returns TypedDict entities for ORM independence.
"""

from typing import Optional
from uuid import UUID

from app.models.task import Task
from app.models.project import Project
from app.repositories.base import BaseRepository
from app.domain.entities import TaskData


class TaskRepository(BaseRepository[Task, TaskData]):
    """Repository for task data access."""

    model = Task

    def _to_dict(self, task: Task) -> TaskData:
        """Convert Task ORM instance to TaskData dict."""
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "project_id": task.project_id,
            "project_name": task.project.name,
            "is_active": task.is_active,
            "created_at": task.created_at,
        }

    async def create(
        self,
        name: str,
        description: Optional[str],
        project_id: str
    ) -> TaskData:
        """
        Create new task in project.

        Args:
            name: Task name
            description: Task description (optional)
            project_id: Project UUID (as string)

        Returns:
            Task data dict with project_name
        """
        # Get Project ORM object for foreign key (repository handles ORM)
        project = await Project.get(id=project_id)

        task = await self.model.create(
            name=name,
            description=description,
            project=project
        )

        # Prefetch project for project_name extraction
        await task.fetch_related('project')

        # Convert ORM → TaskData dict using _to_dict
        return self._to_dict(task)

    async def get_by_id(
        self,
        task_id: str,
        org_id: str
    ) -> Optional[TaskData]:
        """
        Get task by ID with multi-tenant filtering.

        Args:
            task_id: Task UUID
            org_id: Organization UUID

        Returns:
            Task data dict with project_name, or None if not found or wrong org
        """
        task = await self.model.filter(
            id=task_id,
            project__organization_id=org_id  # Multi-tenant filter via project
        ).prefetch_related('project').first()

        if not task:
            return None

        # Convert ORM → TaskData dict using _to_dict
        return self._to_dict(task)

    async def list(
        self,
        org_id: UUID | str,
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """
        List tasks with filtering and pagination.

        Args:
            org_id: Organization UUID
            filters: Dict with optional keys: project_id (UUID), is_active (bool)
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with keys: items (list of TaskData dicts), total (int)
        """
        # Base query with org filter
        query = self.model.filter(project__organization_id=org_id)

        # Apply optional filters
        if 'project_id' in filters and filters['project_id'] is not None:
            query = query.filter(project_id=filters['project_id'])

        if 'is_active' in filters and filters['is_active'] is not None:
            query = query.filter(is_active=filters['is_active'])

        # Get total count
        total = await query.count()

        # Get paginated results with project prefetched
        tasks = await query.prefetch_related('project').offset(offset).limit(limit).all()

        # Convert ORM objects → TaskData dicts
        items = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "project_id": t.project_id,
                "project_name": t.project.name,
                "is_active": t.is_active,
                "created_at": t.created_at,
            }
            for t in tasks
        ]

        return {
            "items": items,
            "total": total
        }

    async def update(
        self,
        task_id: str,
        org_id: UUID | str,
        data: dict
    ) -> Optional[TaskData]:
        """
        Update task with multi-tenant filtering.

        Note: Cannot update project_id (not in data dict from TaskUpdate schema)

        Args:
            task_id: Task UUID
            org_id: Organization UUID
            data: Dict of fields to update

        Returns:
            Updated task data dict, or None if not found
        """
        # Get task (verifies org ownership via project)
        task = await self.model.filter(
            id=task_id,
            project__organization_id=org_id
        ).first()

        if not task:
            return None

        # Update fields
        for key, value in data.items():
            setattr(task, key, value)

        await task.save()

        # Fetch with project for conversion
        task = await self.model.filter(
            id=task_id,
            project__organization_id=org_id
        ).prefetch_related('project').first()

        # Convert ORM → TaskData dict using _to_dict
        return self._to_dict(task)

    async def soft_delete(
        self,
        task_id: str,
        org_id: str
    ) -> bool:
        """
        Soft delete task (set is_active=False).

        Args:
            task_id: Task UUID
            org_id: Organization UUID

        Returns:
            True if deleted, False if not found
        """
        task = await self.model.filter(
            id=task_id,
            project__organization_id=org_id
        ).first()

        if not task:
            return False

        task.is_active = False
        await task.save()

        return True


# Singleton instance
task_repo = TaskRepository()
