"""
Tests for ProjectRepository.

Tests CRUD operations and multi-tenant isolation.
"""

import pytest

from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


class TestProjectRepository:
    """Test ProjectRepository methods."""

    async def test_create_project(self, test_org):
        """Test creating a project."""
        project = await project_repo.create(
            name="New Project",
            description="Test description",
            color="#3b82f6",
            org_id=test_org["id"]
        )

        assert project["id"] is not None
        assert project["name"] == "New Project"
        assert project["description"] == "Test description"
        assert project["organization_id"] == test_org["id"]
        assert project["is_active"] is True
        assert project["task_count"] == 0  # New project has no tasks

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_get_by_id_success(self, test_org):
        """Test getting project by ID."""
        # Create project via repository
        created_project = await project_repo.create(
            name="Test Project",
            description="Test description",
            color="#10b981",
            org_id=test_org["id"]
        )

        # Get by ID
        project = await project_repo.get_by_id(
            created_project["id"],
            test_org["id"]
        )

        assert project is not None
        assert project["id"] == created_project["id"]
        assert project["name"] == "Test Project"
        assert project["task_count"] == 0

        # Cleanup
        await project_repo.delete(created_project["id"])

    async def test_get_by_id_returns_task_count(self, test_org):
        """Test that get_by_id includes accurate task_count."""
        # Create project via repository
        created_project = await project_repo.create(
            name="Test Project",
            description=None,
            color="#f59e0b",
            org_id=test_org["id"]
        )

        # Create some tasks via repository
        task1 = await task_repo.create(name="Task 1", description=None, project_id=created_project["id"])
        task2 = await task_repo.create(name="Task 2", description=None, project_id=created_project["id"])

        # Get project
        project = await project_repo.get_by_id(
            created_project["id"],
            test_org["id"]
        )

        assert project is not None
        assert project["task_count"] == 2

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await project_repo.delete(created_project["id"])

    async def test_get_by_id_wrong_org_returns_none(self, test_org, second_org):
        """Test multi-tenant isolation - wrong org returns None."""
        # Create project in test_org
        created_project = await project_repo.create(
            name="Test Project",
            description=None,
            color="#8b5cf6",
            org_id=test_org["id"]
        )

        # Try to get with wrong org_id
        project = await project_repo.get_by_id(
            created_project["id"],
            second_org["id"]  # Wrong org
        )

        assert project is None  # Should not be accessible

        # Cleanup
        await project_repo.delete(created_project["id"])

    async def test_list_projects(self, test_org):
        """Test listing projects in an organization."""
        # Create multiple projects via repository
        project1 = await project_repo.create(name="Project 1", description=None, color="#3b82f6", org_id=test_org["id"])
        project2 = await project_repo.create(name="Project 2", description=None, color="#10b981", org_id=test_org["id"])
        project3 = await project_repo.create(name="Project 3", description=None, color="#f59e0b", org_id=test_org["id"])

        # List projects
        result = await project_repo.list(
            org_id=test_org["id"],
            filters={},
            limit=10,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3

        # Cleanup
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])
        await project_repo.delete(project3["id"])

    async def test_list_filter_by_is_active(self, test_org):
        """Test filtering projects by is_active status."""
        # Create active project
        active_project = await project_repo.create(
            name="Active Project",
            description=None,
            color="#3b82f6",
            org_id=test_org["id"]
        )

        # Create inactive project
        inactive_project = await project_repo.create(
            name="Inactive Project",
            description=None,
            color="#ef4444",
            org_id=test_org["id"]
        )
        # Soft delete to make inactive
        await project_repo.soft_delete(inactive_project["id"], test_org["id"])

        # Filter for active only
        result = await project_repo.list(
            org_id=test_org["id"],
            filters={"is_active": True},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Active Project"

        # Filter for inactive only
        result = await project_repo.list(
            org_id=test_org["id"],
            filters={"is_active": False},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Inactive Project"

        # Cleanup
        await project_repo.delete(active_project["id"])
        await project_repo.delete(inactive_project["id"])

    async def test_update_project(self, test_org):
        """Test updating project fields."""
        # Create project
        project = await project_repo.create(
            name="Original Name",
            description="Original description",
            color="#3b82f6",
            org_id=test_org["id"]
        )

        # Update project
        updated = await project_repo.update(
            project["id"],
            test_org["id"],
            {"name": "Updated Name", "description": "Updated description"}
        )

        assert updated is not None
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Updated description"

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_update_wrong_org_returns_none(self, test_org, second_org):
        """Test multi-tenant isolation on update."""
        # Create project in test_org
        project = await project_repo.create(
            name="Test Project",
            description=None,
            color="#10b981",
            org_id=test_org["id"]
        )

        # Try to update from second_org
        updated = await project_repo.update(
            project["id"],
            second_org["id"],  # Wrong org
            {"name": "Should Not Update"}
        )

        assert updated is None  # Should not be accessible

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_soft_delete(self, test_org):
        """Test soft deleting project (sets is_active=False)."""
        # Create project
        project = await project_repo.create(
            name="Test Project",
            description=None,
            color="#f59e0b",
            org_id=test_org["id"]
        )

        # Soft delete
        deleted = await project_repo.soft_delete(project["id"], test_org["id"])
        assert deleted is True

        # Verify it's marked inactive
        fetched = await project_repo.get_by_id(project["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is False

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_soft_delete_wrong_org_returns_false(self, test_org, second_org):
        """Test multi-tenant isolation on soft delete."""
        # Create project in test_org
        project = await project_repo.create(
            name="Test Project",
            description=None,
            color="#8b5cf6",
            org_id=test_org["id"]
        )

        # Try to soft delete from second_org
        deleted = await project_repo.soft_delete(project["id"], second_org["id"])
        assert deleted is False  # Should not be accessible

        # Verify it's still active
        fetched = await project_repo.get_by_id(project["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is True

        # Cleanup
        await project_repo.delete(project["id"])
