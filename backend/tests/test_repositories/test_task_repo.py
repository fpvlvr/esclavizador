"""
Tests for TaskRepository.

Tests CRUD operations and multi-tenant isolation via project.
"""

import pytest

from app.models.organization import Organization
from app.models.project import Project
from app.models.task import Task
from app.repositories.task_repo import task_repo


class TestTaskRepository:
    """Test TaskRepository methods."""

    async def test_create_task(self, test_org):
        """Test creating a task."""
        # Create project first
        project = await Project.create(
            name="Test Project",
            organization=test_org
        )

        # Create task
        task = await task_repo.create(
            name="New Task",
            description="Test description",
            project=project
        )

        assert task.id is not None
        assert task.name == "New Task"
        assert task.description == "Test description"
        assert task.project_id == project.id
        assert task.is_active is True
        assert task.project.name == "Test Project"  # Prefetched

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_get_by_id_success(self, test_org):
        """Test getting task by ID with project_name."""
        # Create project and task
        project = await Project.create(
            name="Test Project",
            organization=test_org
        )
        created_task = await Task.create(
            name="Test Task",
            description="Test description",
            project=project
        )

        # Get by ID
        task = await task_repo.get_by_id(
            str(created_task.id),
            str(test_org.id)
        )

        assert task is not None
        assert task.id == created_task.id
        assert task.name == "Test Task"
        assert task.project.name == "Test Project"  # Prefetched

        # Cleanup
        await created_task.delete()
        await project.delete()

    async def test_get_by_id_wrong_org_returns_none(self, test_org):
        """Test multi-tenant isolation - wrong org returns None."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project and task in test_org
        project = await Project.create(
            name="Test Project",
            organization=test_org
        )
        created_task = await Task.create(
            name="Test Task",
            project=project
        )

        # Try to get with wrong org_id
        task = await task_repo.get_by_id(
            str(created_task.id),
            str(second_org.id)  # Wrong org
        )

        assert task is None  # Multi-tenant isolation working

        # Cleanup
        await created_task.delete()
        await project.delete()
        await second_org.delete()

    async def test_list_tasks(self, test_org):
        """Test listing tasks with pagination."""
        # Create project and multiple tasks
        project = await Project.create(name="Test Project", organization=test_org)
        task1 = await Task.create(name="Task 1", project=project)
        task2 = await Task.create(name="Task 2", project=project)
        task3 = await Task.create(name="Task 3", project=project)

        # List all
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={},
            limit=10,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["items"][0].project.name == "Test Project"  # Prefetched

        # Test pagination
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={},
            limit=2,
            offset=0
        )

        assert result["total"] == 3
        assert len(result["items"]) == 2

        # Cleanup
        await task1.delete()
        await task2.delete()
        await task3.delete()
        await project.delete()

    async def test_list_filter_by_project(self, test_org):
        """Test filtering tasks by project_id."""
        # Create two projects with tasks
        project1 = await Project.create(name="Project 1", organization=test_org)
        project2 = await Project.create(name="Project 2", organization=test_org)

        task1 = await Task.create(name="Task 1", project=project1)
        task2 = await Task.create(name="Task 2", project=project1)
        task3 = await Task.create(name="Task 3", project=project2)

        # Filter by project1
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={"project_id": str(project1.id)},
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert all(task.project_id == project1.id for task in result["items"])

        # Filter by project2
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={"project_id": str(project2.id)},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0].project_id == project2.id

        # Cleanup
        await task1.delete()
        await task2.delete()
        await task3.delete()
        await project1.delete()
        await project2.delete()

    async def test_list_filter_by_is_active(self, test_org):
        """Test filtering tasks by is_active."""
        # Create project with active and inactive tasks
        project = await Project.create(name="Test Project", organization=test_org)

        active_task = await Task.create(
            name="Active Task",
            project=project,
            is_active=True
        )
        inactive_task = await Task.create(
            name="Inactive Task",
            project=project,
            is_active=False
        )

        # Filter by active only
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={"is_active": True},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0].name == "Active Task"

        # Filter by inactive only
        result = await task_repo.list(
            org_id=str(test_org.id),
            filters={"is_active": False},
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0].name == "Inactive Task"

        # Cleanup
        await active_task.delete()
        await inactive_task.delete()
        await project.delete()

    async def test_update_task(self, test_org):
        """Test updating task."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org)
        task = await Task.create(
            name="Original Name",
            description="Original description",
            project=project
        )

        # Update
        updated_task = await task_repo.update(
            task_id=str(task.id),
            org_id=str(test_org.id),
            data={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )

        assert updated_task is not None
        assert updated_task.name == "Updated Name"
        assert updated_task.description == "Updated description"
        assert updated_task.project.name == "Test Project"  # Prefetched

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_update_wrong_org_returns_none(self, test_org):
        """Test multi-tenant isolation on update."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project and task in test_org
        project = await Project.create(name="Test Project", organization=test_org)
        task = await Task.create(name="Test Task", project=project)

        # Try to update with wrong org_id
        updated_task = await task_repo.update(
            task_id=str(task.id),
            org_id=str(second_org.id),  # Wrong org
            data={"name": "Should Not Update"}
        )

        assert updated_task is None

        # Verify original not changed
        task = await Task.get(id=task.id)
        assert task.name == "Test Task"

        # Cleanup
        await task.delete()
        await project.delete()
        await second_org.delete()

    async def test_soft_delete(self, test_org):
        """Test soft deleting task."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org)
        task = await Task.create(
            name="Test Task",
            project=project,
            is_active=True
        )

        # Soft delete
        deleted = await task_repo.soft_delete(
            task_id=str(task.id),
            org_id=str(test_org.id)
        )

        assert deleted is True

        # Verify is_active set to False
        task = await Task.get(id=task.id)
        assert task.is_active is False

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_soft_delete_wrong_org_returns_false(self, test_org):
        """Test multi-tenant isolation on delete."""
        # Create second org
        second_org = await Organization.create(name="Second Org")

        # Create project and task in test_org
        project = await Project.create(name="Test Project", organization=test_org)
        task = await Task.create(
            name="Test Task",
            project=project,
            is_active=True
        )

        # Try to delete with wrong org_id
        deleted = await task_repo.soft_delete(
            task_id=str(task.id),
            org_id=str(second_org.id)  # Wrong org
        )

        assert deleted is False

        # Verify task still active
        task = await Task.get(id=task.id)
        assert task.is_active is True

        # Cleanup
        await task.delete()
        await project.delete()
        await second_org.delete()
