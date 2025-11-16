"""
Project repository for database operations.

Handles all database queries for Project model with multi-tenant isolation.
Returns TypedDict entities for ORM independence.
"""

from typing import Optional
from uuid import UUID
from tortoise.functions import Count

from app.models.project import Project
from app.repositories.base import BaseRepository
from app.domain.entities import ProjectData


class ProjectRepository(BaseRepository[Project, ProjectData]):
    """Repository for project data access."""

    model = Project

    def _to_dict(self, project: Project) -> ProjectData:
        """Convert Project ORM instance to ProjectData dict."""
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "organization_id": project.organization_id,
            "is_active": project.is_active,
            "created_at": project.created_at,
            "task_count": getattr(project, 'task_count', 0),
        }

    async def create(
        self,
        name: str,
        description: Optional[str],
        org_id: str
    ) -> ProjectData:
        """
        Create new project in organization.

        Args:
            name: Project name
            description: Project description (optional)
            org_id: Organization UUID

        Returns:
            Project data dict with task_count=0
        """
        project = await self.model.create(
            name=name,
            description=description,
            organization_id=org_id
        )

        # Convert ORM → ProjectData dict
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "organization_id": project.organization_id,
            "is_active": project.is_active,
            "created_at": project.created_at,
            "task_count": 0,  # New project has no tasks
        }

    async def get_by_id(
        self,
        project_id: str,
        org_id: str
    ) -> Optional[ProjectData]:
        """
        Get project by ID with multi-tenant filtering.

        Args:
            project_id: Project UUID
            org_id: Organization UUID

        Returns:
            Project data dict with task_count, or None if not found or wrong org
        """
        project = await self.model.filter(
            id=project_id,
            organization_id=org_id
        ).annotate(
            task_count=Count('tasks')
        ).first()

        if not project:
            return None

        # Convert ORM → ProjectData dict
        # Note: task_count is added via annotate() and accessed via getattr
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "organization_id": project.organization_id,
            "is_active": project.is_active,
            "created_at": project.created_at,
            "task_count": getattr(project, 'task_count', 0),
        }

    async def list(
        self,
        org_id: UUID | str,
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """
        List projects with filtering and pagination.

        Args:
            org_id: Organization UUID
            filters: Dict with optional keys: is_active (bool)
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with keys: items (list of ProjectData dicts), total (int)
        """
        # Base query with org filter
        query = self.model.filter(organization_id=org_id)

        # Apply optional filters
        if 'is_active' in filters and filters['is_active'] is not None:
            query = query.filter(is_active=filters['is_active'])

        # Get total count
        total = await query.count()

        # Get paginated results with task_count
        projects = await query.annotate(
            task_count=Count('tasks')
        ).offset(offset).limit(limit).all()

        # Convert ORM objects → ProjectData dicts
        items = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "organization_id": p.organization_id,
                "is_active": p.is_active,
                "created_at": p.created_at,
                "task_count": getattr(p, 'task_count', 0),
            }
            for p in projects
        ]

        return {
            "items": items,
            "total": total
        }

    async def update(
        self,
        project_id: str,
        org_id: UUID | str,
        data: dict
    ) -> Optional[ProjectData]:
        """
        Update project with multi-tenant filtering.

        Args:
            project_id: Project UUID
            org_id: Organization UUID
            data: Dict of fields to update

        Returns:
            Updated project data dict, or None if not found
        """
        # Get project (verifies org ownership)
        project = await self.model.filter(
            id=project_id,
            organization_id=org_id
        ).first()

        if not project:
            return None

        # Update fields
        for key, value in data.items():
            setattr(project, key, value)

        await project.save()

        # Fetch with task_count for conversion
        project = await self.model.filter(
            id=project_id,
            organization_id=org_id
        ).annotate(
            task_count=Count('tasks')
        ).first()

        # Convert ORM → ProjectData dict using _to_dict
        return self._to_dict(project)

    async def soft_delete(
        self,
        project_id: str,
        org_id: str
    ) -> bool:
        """
        Soft delete project (set is_active=False).

        Args:
            project_id: Project UUID
            org_id: Organization UUID

        Returns:
            True if deleted, False if not found
        """
        project = await self.model.filter(
            id=project_id,
            organization_id=org_id
        ).first()

        if not project:
            return False

        project.is_active = False
        await project.save()

        return True


# Singleton instance
project_repo = ProjectRepository()
