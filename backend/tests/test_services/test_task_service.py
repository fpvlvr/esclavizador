"""
Tests for TaskService.

Tests business logic, authorization, project validation, and multi-tenant enforcement.
"""

import pytest
from fastapi import HTTPException

from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import task_service
from app.repositories.task_repo import task_repo


class TestTaskService:
    """Test TaskService methods."""

    async def test_create_task(self, test_boss, test_project):
        """Test creating task with valid project."""
        # Create task
        data = TaskCreate(
            name="New Task",
            description="Test description",
            project_id=test_project["id"]
        )

        task = await task_service.create_task(test_boss, data)

        assert task["id"] is not None
        assert task["name"] == "New Task"
        assert task["description"] == "Test description"
        assert task["project_id"] == test_project["id"]
        assert task["project_name"] == "Test Project"  # From fixture

        # Cleanup via repository
        await task_repo.delete(task["id"])

    async def test_create_task_invalid_project(self, test_boss):
        """Test creating task with non-existent project."""
        data = TaskCreate(
            name="New Task",
            project_id="00000000-0000-0000-0000-000000000000"
        )

        with pytest.raises(HTTPException) as exc_info:
            await task_service.create_task(test_boss, data)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_create_task_project_wrong_org(self, test_boss, second_org_project):
        """Test creating task with project from different org."""
        # Try to create task as test_boss (different org) using second_org_project
        data = TaskCreate(
            name="New Task",
            project_id=second_org_project["id"]
        )

        with pytest.raises(HTTPException) as exc_info:
            await task_service.create_task(test_boss, data)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_list_tasks(self, test_worker, test_project):
        """Test listing tasks."""
        # Create tasks in test_project via repository
        task1 = await task_repo.create(name="Task 1", description=None, project_id=test_project["id"])
        task2 = await task_repo.create(name="Task 2", description=None, project_id=test_project["id"])

        result = await task_service.list_tasks(
            user=test_worker,
            project_id=None,
            is_active=None,
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["project_name"] == "Test Project"  # From fixture

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])

    async def test_list_tasks_filter_by_project(self, test_worker, test_org):
        """Test filtering tasks by project_id."""
        # Create a second project in same org for testing filtering
        from app.repositories.project_repo import project_repo

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
        result = await task_service.list_tasks(
            user=test_worker,
            project_id=project1["id"],
            is_active=None,
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert all(t["project_id"] == project1["id"] for t in result["items"])

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await task_repo.delete(task3["id"])
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])

    async def test_list_tasks_invalid_project_filter(self, test_worker):
        """Test filtering by non-existent project raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.list_tasks(
                user=test_worker,
                project_id="00000000-0000-0000-0000-000000000000",
                is_active=None,
                limit=10,
                offset=0
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_list_tasks_filter_by_is_active(self, test_worker, test_org, test_project):
        """Test filtering tasks by is_active."""
        # Create active and inactive tasks via repository
        active = await task_repo.create(name="Active", description=None, project_id=test_project["id"])
        inactive = await task_repo.create(name="Inactive", description=None, project_id=test_project["id"])
        # Soft delete to make inactive
        await task_repo.soft_delete(inactive["id"], test_org["id"])

        # Filter active only
        result = await task_service.list_tasks(
            user=test_worker,
            project_id=None,
            is_active=True,
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Active"

        # Cleanup
        await task_repo.delete(active["id"])
        await task_repo.delete(inactive["id"])

    async def test_get_task_success(self, test_worker, test_project):
        """Test getting task by ID with project_name."""
        # Create task via repository
        created = await task_repo.create(
            name="Test Task",
            description="Test desc",
            project_id=test_project["id"]
        )

        # Get it
        task = await task_service.get_task(test_worker, created["id"])

        assert task["id"] == created["id"]
        assert task["name"] == "Test Task"
        assert task["project_name"] == "Test Project"  # From fixture

        # Cleanup
        await task_repo.delete(created["id"])

    async def test_get_task_not_found(self, test_worker):
        """Test 404 when task doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.get_task(
                test_worker,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"

    async def test_get_task_wrong_org_raises_404(self, test_worker, second_org_project):
        """Test multi-tenant isolation raises 404."""
        # Create task in second_org_project via repository
        task = await task_repo.create(
            name="Other Task",
            description=None,
            project_id=second_org_project["id"]
        )

        # Try to get as test_worker (different org)
        with pytest.raises(HTTPException) as exc_info:
            await task_service.get_task(test_worker, task["id"])

        assert exc_info.value.status_code == 404

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_update_task(self, test_boss, test_project):
        """Test updating task."""
        # Create task via repository
        task = await task_repo.create(
            name="Original",
            description="Original desc",
            project_id=test_project["id"]
        )

        # Update
        data = TaskUpdate(
            name="Updated",
            description="Updated desc"
        )
        updated = await task_service.update_task(
            test_boss,
            task["id"],
            data
        )

        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated desc"
        assert updated["project_name"] == "Test Project"  # From fixture

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_update_task_partial(self, test_boss, test_project):
        """Test partial update."""
        # Create task via repository
        task = await task_repo.create(
            name="Original",
            description="Original desc",
            project_id=test_project["id"]
        )

        # Update only name
        data = TaskUpdate(name="Updated Name")
        updated = await task_service.update_task(
            test_boss,
            task["id"],
            data
        )

        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Original desc"  # Unchanged

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_update_not_found(self, test_boss):
        """Test 404 when updating non-existent task."""
        data = TaskUpdate(name="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await task_service.update_task(
                test_boss,
                "00000000-0000-0000-0000-000000000000",
                data
            )

        assert exc_info.value.status_code == 404

    async def test_update_wrong_org_raises_404(self, test_boss, second_org_project):
        """Test multi-tenant isolation on update."""
        # Create task in second_org_project via repository
        task = await task_repo.create(
            name="Other Task",
            description=None,
            project_id=second_org_project["id"]
        )

        # Try to update as test_boss (different org)
        data = TaskUpdate(name="Should Not Work")
        with pytest.raises(HTTPException) as exc_info:
            await task_service.update_task(test_boss, task["id"], data)

        assert exc_info.value.status_code == 404

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_delete_task(self, test_boss, test_org, test_project):
        """Test soft deleting task."""
        # Create task via repository
        task = await task_repo.create(
            name="Test Task",
            description=None,
            project_id=test_project["id"]
        )

        # Delete
        result = await task_service.delete_task(test_boss, task["id"])

        assert result is True

        # Verify soft deleted via repository
        fetched = await task_repo.get_by_id(task["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is False

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_delete_not_found(self, test_boss):
        """Test 404 when deleting non-existent task."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.delete_task(
                test_boss,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404

    async def test_delete_wrong_org_raises_404(self, test_boss, second_org, second_org_project):
        """Test multi-tenant isolation on delete."""
        # Create task in second_org_project via repository
        task = await task_repo.create(
            name="Other Task",
            description=None,
            project_id=second_org_project["id"]
        )

        # Try to delete as test_boss (different org)
        with pytest.raises(HTTPException) as exc_info:
            await task_service.delete_task(test_boss, task["id"])

        assert exc_info.value.status_code == 404

        # Verify not deleted via repository
        fetched = await task_repo.get_by_id(task["id"], second_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is True

        # Cleanup
        await task_repo.delete(task["id"])
