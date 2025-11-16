"""
Tests for ProjectService.

Tests business logic, authorization, and multi-tenant enforcement.
"""

import pytest
from fastapi import HTTPException

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.task import Task
from app.core.security import hash_password
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import project_service


class TestProjectService:
    """Test ProjectService methods."""

    async def test_create_project(self, test_master, test_org):
        """Test creating project."""
        data = ProjectCreate(
            name="New Project",
            description="Test description"
        )

        project = await project_service.create_project(test_master, data)

        assert project["id"] is not None
        assert project["name"] == "New Project"
        assert project["description"] == "Test description"
        assert project["organization_id"] == test_org["id"]
        assert project["task_count"] == 0

        # Cleanup - project is dict, delete via ORM
        await Project.get(id=project["id"]).delete()

    async def test_list_projects(self, test_user, test_org_orm):
        """Test listing projects."""
        # Create some projects using ORM fixture
        project1 = await Project.create(name="Project 1", organization=test_org_orm)
        project2 = await Project.create(name="Project 2", organization=test_org_orm)

        result = await project_service.list_projects(
            user=test_user,
            is_active=None,
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["limit"] == 10
        assert result["offset"] == 0

        # Cleanup
        await project1.delete()
        await project2.delete()

    async def test_list_filter_by_is_active(self, test_user, test_org_orm):
        """Test filtering by is_active."""
        # Create active and inactive projects
        active = await Project.create(
            name="Active",
            organization=test_org_orm,
            is_active=True
        )
        inactive = await Project.create(
            name="Inactive",
            organization=test_org_orm,
            is_active=False
        )

        # Filter active only
        result = await project_service.list_projects(
            user=test_user,
            is_active=True,
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Active"

        # Cleanup
        await active.delete()
        await inactive.delete()

    async def test_get_project_success(self, test_user, test_org_orm):
        """Test getting project by ID."""
        # Create project
        created = await Project.create(
            name="Test Project",
            organization=test_org_orm
        )

        # Get it
        project = await project_service.get_project(test_user, str(created.id))

        assert project["id"] == created.id
        assert project["name"] == "Test Project"
        assert project["task_count"] == 0

        # Cleanup
        await created.delete()

    async def test_get_project_not_found(self, test_user):
        """Test 404 when project doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await project_service.get_project(
                test_user,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_get_project_wrong_org_raises_404(self, test_user, second_org_orm):
        """Test multi-tenant isolation raises 404."""
        # Create project in second org
        project = await Project.create(
            name="Other Org Project",
            organization=second_org_orm
        )

        # Try to get it as test_user (different org)
        with pytest.raises(HTTPException) as exc_info:
            await project_service.get_project(test_user, str(project.id))

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

        # Cleanup
        await project.delete()

    async def test_update_project(self, test_master, test_org_orm):
        """Test updating project."""
        # Create project
        project = await Project.create(
            name="Original",
            description="Original desc",
            organization=test_org_orm
        )

        # Update
        data = ProjectUpdate(
            name="Updated",
            description="Updated desc"
        )
        updated = await project_service.update_project(
            test_master,
            str(project.id),
            data
        )

        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated desc"
        assert updated["task_count"] == 0

        # Cleanup
        await project.delete()

    async def test_update_project_partial(self, test_master, test_org_orm):
        """Test partial update (only some fields)."""
        # Create project
        project = await Project.create(
            name="Original",
            description="Original desc",
            organization=test_org_orm
        )

        # Update only name
        data = ProjectUpdate(name="Updated Name")
        updated = await project_service.update_project(
            test_master,
            str(project.id),
            data
        )

        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Original desc"  # Unchanged

        # Cleanup
        await project.delete()

    async def test_update_not_found(self, test_master):
        """Test 404 when updating non-existent project."""
        data = ProjectUpdate(name="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await project_service.update_project(
                test_master,
                "00000000-0000-0000-0000-000000000000",
                data
            )

        assert exc_info.value.status_code == 404

    async def test_update_wrong_org_raises_404(self, test_master, second_org_orm):
        """Test multi-tenant isolation on update."""
        # Create project in second org
        project = await Project.create(
            name="Other Org Project",
            organization=second_org_orm
        )

        # Try to update as test_master (different org)
        data = ProjectUpdate(name="Should Not Work")
        with pytest.raises(HTTPException) as exc_info:
            await project_service.update_project(
                test_master,
                str(project.id),
                data
            )

        assert exc_info.value.status_code == 404

        # Cleanup
        await project.delete()

    async def test_delete_project(self, test_master, test_org_orm):
        """Test soft deleting project."""
        # Create project
        project = await Project.create(
            name="Test Project",
            organization=test_org_orm,
            is_active=True
        )

        # Delete
        result = await project_service.delete_project(
            test_master,
            str(project.id)
        )

        assert result is True

        # Verify soft deleted
        project = await Project.get(id=project.id)
        assert project.is_active is False

        # Cleanup
        await project.delete()

    async def test_delete_not_found(self, test_master):
        """Test 404 when deleting non-existent project."""
        with pytest.raises(HTTPException) as exc_info:
            await project_service.delete_project(
                test_master,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404

    async def test_delete_wrong_org_raises_404(self, test_master, second_org_orm):
        """Test multi-tenant isolation on delete."""
        # Create project in second org
        project = await Project.create(
            name="Other Org Project",
            organization=second_org_orm
        )

        # Try to delete as test_master (different org)
        with pytest.raises(HTTPException) as exc_info:
            await project_service.delete_project(test_master, str(project.id))

        assert exc_info.value.status_code == 404

        # Verify not deleted
        project = await Project.get(id=project.id)
        assert project.is_active is True

        # Cleanup
        await project.delete()

    async def test_pagination(self, test_user, test_org_orm):
        """Test pagination with limit and offset."""
        # Create multiple projects
        projects = []
        for i in range(5):
            p = await Project.create(name=f"Project {i}", organization=test_org_orm)
            projects.append(p)

        # Get first 2
        result = await project_service.list_projects(
            user=test_user,
            is_active=None,
            limit=2,
            offset=0
        )

        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["limit"] == 2
        assert result["offset"] == 0

        # Get next 2
        result = await project_service.list_projects(
            user=test_user,
            is_active=None,
            limit=2,
            offset=2
        )

        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["offset"] == 2

        # Cleanup
        for p in projects:
            await p.delete()

    async def test_task_count_accuracy(self, test_user, test_org_orm):
        """Test task_count is computed correctly."""
        # Create project
        project = await Project.create(name="Test Project", organization=test_org_orm)

        # Initially no tasks
        result = await project_service.get_project(test_user, str(project.id))
        assert result["task_count"] == 0

        # Add tasks
        task1 = await Task.create(name="Task 1", project=project)
        task2 = await Task.create(name="Task 2", project=project)

        # Should show 2 tasks
        result = await project_service.get_project(test_user, str(project.id))
        assert result["task_count"] == 2

        # Cleanup
        await task1.delete()
        await task2.delete()
        await project.delete()
