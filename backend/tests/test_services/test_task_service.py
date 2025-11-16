"""
Tests for TaskService.

Tests business logic, authorization, project validation, and multi-tenant enforcement.
"""

import pytest
from fastapi import HTTPException

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.task import Task
from app.core.security import hash_password
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import task_service


class TestTaskService:
    """Test TaskService methods."""

    async def test_create_task(self, test_master, test_org_orm):
        """Test creating task with valid project."""
        # Create project
        project = await Project.create(name="Test Project", organization=test_org_orm)

        # Create task
        data = TaskCreate(
            name="New Task",
            description="Test description",
            project_id=project.id
        )

        task = await task_service.create_task(test_master, data)

        assert task["id"] is not None
        assert task["name"] == "New Task"
        assert task["description"] == "Test description"
        assert task["project_id"] == project.id
        assert task["project_name"] == "Test Project"  # Extracted from project

        # Cleanup - task is dict, delete via ORM
        await Task.get(id=task["id"]).delete()
        await project.delete()

    async def test_create_task_invalid_project(self, test_master):
        """Test creating task with non-existent project."""
        data = TaskCreate(
            name="New Task",
            project_id="00000000-0000-0000-0000-000000000000"
        )

        with pytest.raises(HTTPException) as exc_info:
            await task_service.create_task(test_master, data)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_create_task_project_wrong_org(self, test_master, second_org_orm):
        """Test creating task with project from different org."""
        # Create project in second org
        project = await Project.create(
            name="Other Org Project",
            organization=second_org_orm
        )

        # Try to create task as test_master (different org)
        data = TaskCreate(
            name="New Task",
            project_id=project.id
        )

        with pytest.raises(HTTPException) as exc_info:
            await task_service.create_task(test_master, data)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

        # Cleanup
        await project.delete()

    async def test_list_tasks(self, test_user, test_org_orm):
        """Test listing tasks."""
        # Create project with tasks
        project = await Project.create(name="Test Project", organization=test_org_orm)
        task1 = await Task.create(name="Task 1", project=project)
        task2 = await Task.create(name="Task 2", project=project)

        result = await task_service.list_tasks(
            user=test_user,
            project_id=None,
            is_active=None,
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["project_name"] == "Test Project"  # Extracted from project

        # Cleanup
        await task1.delete()
        await task2.delete()
        await project.delete()

    async def test_list_tasks_filter_by_project(self, test_user, test_org_orm):
        """Test filtering tasks by project_id."""
        # Create two projects with tasks
        project1 = await Project.create(name="Project 1", organization=test_org_orm)
        project2 = await Project.create(name="Project 2", organization=test_org_orm)

        task1 = await Task.create(name="Task 1", project=project1)
        task2 = await Task.create(name="Task 2", project=project1)
        task3 = await Task.create(name="Task 3", project=project2)

        # Filter by project1
        result = await task_service.list_tasks(
            user=test_user,
            project_id=str(project1.id),
            is_active=None,
            limit=10,
            offset=0
        )

        assert result["total"] == 2
        assert all(t["project_id"] == project1.id for t in result["items"])

        # Cleanup
        await task1.delete()
        await task2.delete()
        await task3.delete()
        await project1.delete()
        await project2.delete()

    async def test_list_tasks_invalid_project_filter(self, test_user):
        """Test filtering by non-existent project raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.list_tasks(
                user=test_user,
                project_id="00000000-0000-0000-0000-000000000000",
                is_active=None,
                limit=10,
                offset=0
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Project not found"

    async def test_list_tasks_filter_by_is_active(self, test_user, test_org_orm):
        """Test filtering tasks by is_active."""
        # Create project with active and inactive tasks
        project = await Project.create(name="Test Project", organization=test_org_orm)
        active = await Task.create(name="Active", project=project, is_active=True)
        inactive = await Task.create(name="Inactive", project=project, is_active=False)

        # Filter active only
        result = await task_service.list_tasks(
            user=test_user,
            project_id=None,
            is_active=True,
            limit=10,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["name"] == "Active"

        # Cleanup
        await active.delete()
        await inactive.delete()
        await project.delete()

    async def test_get_task_success(self, test_user, test_org_orm):
        """Test getting task by ID with project_name."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org_orm)
        created = await Task.create(
            name="Test Task",
            description="Test desc",
            project=project
        )

        # Get it
        task = await task_service.get_task(test_user, str(created.id))

        assert task["id"] == created.id
        assert task["name"] == "Test Task"
        assert task["project_name"] == "Test Project"

        # Cleanup
        await created.delete()
        await project.delete()

    async def test_get_task_not_found(self, test_user):
        """Test 404 when task doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.get_task(
                test_user,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Task not found"

    async def test_get_task_wrong_org_raises_404(self, test_user, second_org_orm):
        """Test multi-tenant isolation raises 404."""
        # Create project and task in second org
        project = await Project.create(name="Other Project", organization=second_org_orm)
        task = await Task.create(name="Other Task", project=project)

        # Try to get as test_user (different org)
        with pytest.raises(HTTPException) as exc_info:
            await task_service.get_task(test_user, str(task.id))

        assert exc_info.value.status_code == 404

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_update_task(self, test_master, test_org_orm):
        """Test updating task."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org_orm)
        task = await Task.create(
            name="Original",
            description="Original desc",
            project=project
        )

        # Update
        data = TaskUpdate(
            name="Updated",
            description="Updated desc"
        )
        updated = await task_service.update_task(
            test_master,
            str(task.id),
            data
        )

        assert updated["name"] == "Updated"
        assert updated["description"] == "Updated desc"
        assert updated["project_name"] == "Test Project"

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_update_task_partial(self, test_master, test_org_orm):
        """Test partial update."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org_orm)
        task = await Task.create(
            name="Original",
            description="Original desc",
            project=project
        )

        # Update only name
        data = TaskUpdate(name="Updated Name")
        updated = await task_service.update_task(
            test_master,
            str(task.id),
            data
        )

        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Original desc"  # Unchanged

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_update_not_found(self, test_master):
        """Test 404 when updating non-existent task."""
        data = TaskUpdate(name="Updated")

        with pytest.raises(HTTPException) as exc_info:
            await task_service.update_task(
                test_master,
                "00000000-0000-0000-0000-000000000000",
                data
            )

        assert exc_info.value.status_code == 404

    async def test_update_wrong_org_raises_404(self, test_master, second_org_orm):
        """Test multi-tenant isolation on update."""
        # Create project and task in second org
        project = await Project.create(name="Other Project", organization=second_org_orm)
        task = await Task.create(name="Other Task", project=project)

        # Try to update as test_master (different org)
        data = TaskUpdate(name="Should Not Work")
        with pytest.raises(HTTPException) as exc_info:
            await task_service.update_task(test_master, str(task.id), data)

        assert exc_info.value.status_code == 404

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_delete_task(self, test_master, test_org_orm):
        """Test soft deleting task."""
        # Create project and task
        project = await Project.create(name="Test Project", organization=test_org_orm)
        task = await Task.create(name="Test Task", project=project, is_active=True)

        # Delete
        result = await task_service.delete_task(test_master, str(task.id))

        assert result is True

        # Verify soft deleted
        task = await Task.get(id=task.id)
        assert task.is_active is False

        # Cleanup
        await task.delete()
        await project.delete()

    async def test_delete_not_found(self, test_master):
        """Test 404 when deleting non-existent task."""
        with pytest.raises(HTTPException) as exc_info:
            await task_service.delete_task(
                test_master,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404

    async def test_delete_wrong_org_raises_404(self, test_master, second_org_orm):
        """Test multi-tenant isolation on delete."""
        # Create project and task in second org
        project = await Project.create(name="Other Project", organization=second_org_orm)
        task = await Task.create(name="Other Task", project=project)

        # Try to delete as test_master (different org)
        with pytest.raises(HTTPException) as exc_info:
            await task_service.delete_task(test_master, str(task.id))

        assert exc_info.value.status_code == 404

        # Verify not deleted
        task = await Task.get(id=task.id)
        assert task.is_active is True

        # Cleanup
        await task.delete()
        await project.delete()
