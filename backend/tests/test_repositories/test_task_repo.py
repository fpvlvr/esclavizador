"""
Tests for TaskRepository.

Tests CRUD operations and multi-tenant isolation via project.
"""

import pytest

from app.repositories.task_repo import task_repo
from app.repositories.project_repo import project_repo


class TestTaskRepository:
    """Test TaskRepository methods."""

    async def test_create_task(self, test_org):
        """Test creating a task."""
        # Create project first via repository
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )

        # Create task
        task = await task_repo.create(
            name="New Task",
            description="Test description",
            project_id=project["id"]
        )

        assert task["id"] is not None
        assert task["name"] == "New Task"
        assert task["description"] == "Test description"
        assert task["project_id"] == project["id"]
        assert task["is_active"] is True
        assert task["project_name"] == "Test Project"  # Extracted from project

        # Cleanup
        await task_repo.delete(task["id"])
        await project_repo.delete(project["id"])

    async def test_get_by_id_success(self, test_org):
        """Test getting task by ID with project_name."""
        # Create project and task via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        created_task = await task_repo.create(
            name="Test Task",
            description="Test description",
            project_id=project["id"]
        )

        # Get by ID
        task = await task_repo.get_by_id(
            created_task["id"],
            test_org["id"]
        )

        assert task is not None
        assert task["id"] == created_task["id"]
        assert task["name"] == "Test Task"
        assert task["project_name"] == "Test Project"  # Extracted from project

        # Cleanup
        await task_repo.delete(created_task["id"])
        await project_repo.delete(project["id"])

    async def test_get_by_id_wrong_org_returns_none(self, test_org, second_org):
        """Test multi-tenant isolation - wrong org returns None."""
        # Create project and task in test_org
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        created_task = await task_repo.create(
            name="Test Task",
            description=None,
            project_id=project["id"]
        )

        # Try to get with wrong org_id
        task = await task_repo.get_by_id(
            created_task["id"],
            second_org["id"]  # Wrong org
        )

        assert task is None  # Multi-tenant isolation working

        # Cleanup
        await task_repo.delete(created_task["id"])
        await project_repo.delete(project["id"])

    async def test_list_tasks(self, test_org):
        """Test listing tasks with pagination."""
        # Create project and multiple tasks via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        task1 = await task_repo.create(name="Task 1", description=None, project_id=project["id"])
        task2 = await task_repo.create(name="Task 2", description=None, project_id=project["id"])
        task3 = await task_repo.create(name="Task 3", description=None, project_id=project["id"])

        # List all
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={},
            limit=10,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["items"][0]["project_name"] == "Test Project"  # Extracted from project

        # Test pagination
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={},
            limit=2,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 2

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await task_repo.delete(task3["id"])
        await project_repo.delete(project["id"])

    async def test_list_filter_by_project(self, test_org):
        """Test filtering tasks by project_id."""
        # Create two projects with tasks via repositories
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

        task1 = await task_repo.create(name="Task 1", description=None, project_id=project1["id"])
        task2 = await task_repo.create(name="Task 2", description=None, project_id=project1["id"])
        task3 = await task_repo.create(name="Task 3", description=None, project_id=project2["id"])

        # Filter by project1
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={"project_id": project1["id"]},
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert all(task["project_id"] == project1["id"] for task in result["items"])

        # Filter by project2
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={"project_id": project2["id"]},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["project_id"] == project2["id"]

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await task_repo.delete(task3["id"])
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])

    async def test_list_filter_by_is_active(self, test_org):
        """Test filtering tasks by is_active."""
        # Create project with active and inactive tasks via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )

        active_task = await task_repo.create(
            name="Active Task",
            description=None,
            project_id=project["id"]
        )
        inactive_task = await task_repo.create(
            name="Inactive Task",
            description=None,
            project_id=project["id"]
        )
        # Soft delete to make inactive
        await task_repo.soft_delete(inactive_task["id"], test_org["id"])

        # Filter by active only
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={"is_active": True},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Active Task"

        # Filter by inactive only
        result = await task_repo.list(
            org_id=test_org["id"],
            filters={"is_active": False},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Inactive Task"

        # Cleanup
        await task_repo.delete(active_task["id"])
        await task_repo.delete(inactive_task["id"])
        await project_repo.delete(project["id"])

    async def test_update_task(self, test_org):
        """Test updating task."""
        # Create project and task via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        task = await task_repo.create(
            name="Original Name",
            description="Original description",
            project_id=project["id"]
        )

        # Update
        updated_task = await task_repo.update(
            task_id=task["id"],
            org_id=test_org["id"],
            data={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )

        assert updated_task is not None
        assert updated_task["name"] == "Updated Name"
        assert updated_task["description"] == "Updated description"
        assert updated_task["project_name"] == "Test Project"  # Extracted from project

        # Cleanup
        await task_repo.delete(task["id"])
        await project_repo.delete(project["id"])

    async def test_update_wrong_org_returns_none(self, test_org, second_org):
        """Test multi-tenant isolation on update."""
        # Create project and task in test_org via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        task = await task_repo.create(
            name="Test Task",
            description=None,
            project_id=project["id"]
        )

        # Try to update with wrong org_id
        updated_task = await task_repo.update(
            task_id=task["id"],
            org_id=second_org["id"],  # Wrong org
            data={"name": "Should Not Update"}
        )

        assert updated_task is None

        # Verify original not changed via repository
        fetched_task = await task_repo.get_by_id(task["id"], test_org["id"])
        assert fetched_task["name"] == "Test Task"

        # Cleanup
        await task_repo.delete(task["id"])
        await project_repo.delete(project["id"])

    async def test_soft_delete(self, test_org):
        """Test soft deleting task."""
        # Create project and task via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        task = await task_repo.create(
            name="Test Task",
            description=None,
            project_id=project["id"]
        )

        # Soft delete
        deleted = await task_repo.soft_delete(
            task_id=task["id"],
            org_id=test_org["id"]
        )

        assert deleted is True

        # Verify is_active set to False via repository
        fetched_task = await task_repo.get_by_id(task["id"], test_org["id"])
        assert fetched_task is not None
        assert fetched_task["is_active"] is False

        # Cleanup
        await task_repo.delete(task["id"])
        await project_repo.delete(project["id"])

    async def test_soft_delete_wrong_org_returns_false(self, test_org, second_org):
        """Test multi-tenant isolation on delete."""
        # Create project and task in test_org via repositories
        project = await project_repo.create(
            name="Test Project",
            description=None,
            org_id=test_org["id"]
        )
        task = await task_repo.create(
            name="Test Task",
            description=None,
            project_id=project["id"]
        )

        # Try to delete with wrong org_id
        deleted = await task_repo.soft_delete(
            task_id=task["id"],
            org_id=second_org["id"]  # Wrong org
        )

        assert deleted is False

        # Verify task still active via repository
        fetched_task = await task_repo.get_by_id(task["id"], test_org["id"])
        assert fetched_task is not None
        assert fetched_task["is_active"] is True

        # Cleanup
        await task_repo.delete(task["id"])
        await project_repo.delete(project["id"])
