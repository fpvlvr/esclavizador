"""
Project service for business logic.

Handles project operations with authorization and multi-tenant enforcement.
"""

from typing import Optional
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.repositories.project_repo import project_repo


class ProjectService:
    """Service for project business logic."""

    async def create_project(
        self,
        user: User,
        data: ProjectCreate
    ):
        """
        Create project in user's organization.

        Args:
            user: Authenticated user (master role verified by dependency)
            data: Project creation data

        Returns:
            Created project with task_count=0
        """
        org_id = str(user.organization_id)

        project = await project_repo.create(
            name=data.name,
            description=data.description,
            org_id=org_id
        )

        return project

    async def list_projects(
        self,
        user: User,
        is_active: Optional[bool],
        limit: int,
        offset: int
    ):
        """
        List projects in user's organization.

        Args:
            user: Authenticated user
            is_active: Optional filter by active status
            limit: Maximum items to return
            offset: Number of items to skip

        Returns:
            Dict with items, total, limit, offset
        """
        org_id = str(user.organization_id)

        filters = {}
        if is_active is not None:
            filters['is_active'] = is_active

        result = await project_repo.list(org_id, filters, limit, offset)

        return {
            "items": result["items"],
            "total": result["total"],
            "limit": limit,
            "offset": offset
        }

    async def get_project(
        self,
        user: User,
        project_id: str
    ):
        """
        Get project by ID (within user's org).

        Args:
            user: Authenticated user
            project_id: Project UUID

        Returns:
            Project with task_count

        Raises:
            HTTPException(404): Project not found
        """
        org_id = str(user.organization_id)
        project = await project_repo.get_by_id(project_id, org_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return project

    async def update_project(
        self,
        user: User,
        project_id: str,
        data: ProjectUpdate
    ):
        """
        Update project (within user's org).

        Args:
            user: Authenticated user (master role verified by dependency)
            project_id: Project UUID
            data: Update data (only provided fields will be updated)

        Returns:
            Updated project with task_count

        Raises:
            HTTPException(404): Project not found
        """
        org_id = str(user.organization_id)

        # Build update dict (only include provided fields)
        update_data = data.model_dump(exclude_unset=True)

        project = await project_repo.update(project_id, org_id, update_data)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return project

    async def delete_project(
        self,
        user: User,
        project_id: str
    ):
        """
        Soft delete project (within user's org).

        Args:
            user: Authenticated user (master role verified by dependency)
            project_id: Project UUID

        Returns:
            True if deleted

        Raises:
            HTTPException(404): Project not found
        """
        org_id = str(user.organization_id)
        deleted = await project_repo.soft_delete(project_id, org_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return True


# Singleton instance
project_service = ProjectService()
