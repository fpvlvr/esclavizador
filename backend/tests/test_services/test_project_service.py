"""
Tests for ProjectService.

Tests business logic, authorization, and multi-tenant enforcement.
"""

import pytest
from fastapi import HTTPException

from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import project_service
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


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

        # Cleanup via repository
        await project_repo.delete(project["id"])

    async def test_list_projects(self, test_user, test_org):
        """Test listing projects."""
        # Create some projects via repository
        project1 = await project_repo.create(
            name="Project 1",
            description=None,
            org_id=test_org["id"]
        )
        project2 = await project_repo.create(
            name="Project 2",
            description=None,
            org_id=test_org["id"]
        )

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
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])

    async def test_list_filter_by_is_active(self, test_user, test_org):
        """Test filtering by is_active."""
        # Create active and inactive projects via repository
        active = await project_repo.create(
            name="Active",
            description=None,
            org_id=test_org["id"]
        )
        inactive = await project_repo.create(
            name="Inactive",
            description=None,
            org_id=test_org["id"]
        )
        # Soft delete to make inactive
        await project_repo.soft_delete(inactive["id"], test_org["id"])

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
        await project_repo.delete(active["id"])
        await project_repo.delete(inactive["id"])

    async def test_get_project_success(self, test_user, test_org):
        """Test getting project by ID."""
        # Create project via repository
        created = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )

        # Get it
        project = await project_service.get_project(test_user, created["id"])

        assert project["id"] == created["id"]
        assert project["name"] == "Test Project"
        assert project["task_count"] == 0

        # Cleanup
        await project_repo.delete(created["id"])

    async def test_get_project_not_found(self, test_user):
        """Test 404 when project doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await project_service.get_project(
                test_user,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_get_project_wrong_org_raises_404(self, test_user, second_org):
        """Test multi-tenant isolation raises 404."""
        # Create project in second org via repository
        project = await project_repo.create(
            name="Other Org Project",
            description=None,
            org_id=second_org["id"]
        )

        # Try to get it as test_user (different org)
        with pytest.raises(HTTPException) as exc_info:
            await project_service.get_project(test_user, project["id"])

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_update_project(self, test_master, test_org):
        """Test updating project."""
        # Create project via repository
        project = await project_repo.create(
            name="Original",
            description="Original desc",
            org_id=test_org["id"]
        )

        # Update
        data = ProjectUpdate(
            name="Updated",
            description="Updated desc"
        )
        updated = await project_service.update_project(
            test_master,
            project["id"],
            data
        )

        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated desc"
        assert updated["task_count"] == 0

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_update_project_partial(self, test_master, test_org):
        """Test partial update (only some fields)."""
        # Create project via repository
        project = await project_repo.create(
            name="Original",
            description="Original desc",
            org_id=test_org["id"]
        )

        # Update only name
        data = ProjectUpdate(name="Updated Name")
        updated = await project_service.update_project(
            test_master,
            project["id"],
            data
        )

        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Original desc"  # Unchanged

        # Cleanup
        await project_repo.delete(project["id"])

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

    async def test_update_wrong_org_raises_404(self, test_master, second_org):
        """Test multi-tenant isolation on update."""
        # Create project in second org via repository
        project = await project_repo.create(
            name="Other Org Project",
            description=None,
            org_id=second_org["id"]
        )

        # Try to update as test_master (different org)
        data = ProjectUpdate(name="Should Not Work")
        with pytest.raises(HTTPException) as exc_info:
            await project_service.update_project(
                test_master,
                project["id"],
                data
            )

        assert exc_info.value.status_code == 404

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_delete_project(self, test_master, test_org):
        """Test soft deleting project."""
        # Create project via repository
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )

        # Delete
        result = await project_service.delete_project(
            test_master,
            project["id"]
        )

        assert result is True

        # Verify soft deleted via repository
        fetched = await project_repo.get_by_id(project["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is False

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_delete_not_found(self, test_master):
        """Test 404 when deleting non-existent project."""
        with pytest.raises(HTTPException) as exc_info:
            await project_service.delete_project(
                test_master,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404

    async def test_delete_wrong_org_raises_404(self, test_master, second_org):
        """Test multi-tenant isolation on delete."""
        # Create project in second org via repository
        project = await project_repo.create(
            name="Other Org Project",
            description=None,
            org_id=second_org["id"]
        )

        # Try to delete as test_master (different org)
        with pytest.raises(HTTPException) as exc_info:
            await project_service.delete_project(test_master, project["id"])

        assert exc_info.value.status_code == 404

        # Verify not deleted via repository
        fetched = await project_repo.get_by_id(project["id"], second_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is True

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_pagination(self, test_user, test_org):
        """Test pagination with limit and offset."""
        # Create multiple projects via repository
        projects = []
        for i in range(5):
            p = await project_repo.create(
                name=f"Project {i}",
                description=None,
                org_id=test_org["id"]
            )
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
            await project_repo.delete(p["id"])

    async def test_task_count_accuracy(self, test_user, test_org):
        """Test task_count is computed correctly."""
        # Create project via repository
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )

        # Initially no tasks
        result = await project_service.get_project(test_user, project["id"])
        assert result["task_count"] == 0

        # Add tasks via repository
        task1 = await task_repo.create(
            name="Task 1",
            description=None,
            project_id=project["id"]
        )
        task2 = await task_repo.create(
            name="Task 2",
            description=None,
            project_id=project["id"]
        )

        # Should show 2 tasks
        result = await project_service.get_project(test_user, project["id"])
        assert result["task_count"] == 2

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await project_repo.delete(project["id"])
