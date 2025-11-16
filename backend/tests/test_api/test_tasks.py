"""
API integration tests for task endpoints.

Tests full HTTP request/response cycle for task CRUD operations.
"""

import pytest

from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


class TestCreateTask:
    """Test POST /api/v1/tasks endpoint."""

    async def test_create_task_as_master(
        self, client, test_master, test_master_email, test_master_password, test_project
    ):
        """Test master can create task."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_master_email,
            "password": test_master_password
        })
        token = login_response.json()["access_token"]

        # Create task
        response = await client.post(
            "/api/v1/tasks",
            json={
                "name": "New Task",
                "description": "Test description",
                "project_id": str(test_project["id"])
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Task"
        assert data["description"] == "Test description"
        assert data["project_id"] == str(test_project["id"])
        assert data["project_name"] == "Test Project"
        assert data["is_active"] is True

    async def test_create_task_as_slave_forbidden(
        self, client, test_slave, test_slave_email, test_slave_password, test_project
    ):
        """Test slave cannot create task (403)."""
        # Login as slave
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Try to create task
        response = await client.post(
            "/api/v1/tasks",
            json={
                "name": "New Task",
                "project_id": str(test_project["id"])
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    async def test_create_task_invalid_project(
        self, client, test_master, test_master_email, test_master_password
    ):
        """Test creating task with non-existent project."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_master_email,
            "password": test_master_password
        })
        token = login_response.json()["access_token"]

        # Create task with invalid project
        response = await client.post(
            "/api/v1/tasks",
            json={
                "name": "New Task",
                "project_id": "00000000-0000-0000-0000-000000000000"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"


class TestListTasks:
    """Test GET /api/v1/tasks endpoint."""

    async def test_list_tasks_as_user(
        self, client, test_slave, test_slave_email, test_slave_password, test_task
    ):
        """Test any user can list tasks."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # List tasks
        response = await client.get(
            "/api/v1/tasks",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert data["items"][0]["project_name"] == "Test Project"

    async def test_list_tasks_filter_by_project(
        self, client, test_slave, test_slave_email, test_slave_password, test_org
    ):
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
        task2 = await task_repo.create(name="Task 2", description=None, project_id=project2["id"])

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Filter by project1
        response = await client.get(
            f"/api/v1/tasks?project_id={project1['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["project_id"] == str(project1["id"])

        # Cleanup
        await task_repo.delete(task1["id"])
        await task_repo.delete(task2["id"])
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])

    async def test_list_tasks_filter_by_is_active(
        self, client, test_slave, test_slave_email, test_slave_password, test_org, test_project
    ):
        """Test filtering tasks by is_active."""
        # Create active and inactive tasks via repository
        active = await task_repo.create(name="Active", description=None, project_id=test_project["id"])
        inactive = await task_repo.create(name="Inactive", description=None, project_id=test_project["id"])
        # Soft delete to make inactive
        await task_repo.soft_delete(inactive["id"], test_org["id"])

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Filter active only
        response = await client.get(
            "/api/v1/tasks?is_active=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(t["is_active"] is True for t in data["items"])

        # Cleanup
        await task_repo.delete(active["id"])
        await task_repo.delete(inactive["id"])


class TestGetTask:
    """Test GET /api/v1/tasks/{id} endpoint."""

    async def test_get_task_success(
        self, client, test_slave, test_slave_email, test_slave_password, test_task
    ):
        """Test getting task by ID."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Get task
        response = await client.get(
            f"/api/v1/tasks/{test_task['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_task["id"])
        assert data["name"] == "Test Task"
        assert "project_name" in data

    async def test_get_task_not_found(
        self, client, test_slave, test_slave_email, test_slave_password
    ):
        """Test 404 when task doesn't exist."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Get non-existent task
        response = await client.get(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestUpdateTask:
    """Test PUT /api/v1/tasks/{id} endpoint."""

    async def test_update_task_as_master(
        self, client, test_master, test_master_email, test_master_password, test_task
    ):
        """Test master can update task."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_master_email,
            "password": test_master_password
        })
        token = login_response.json()["access_token"]

        # Update task
        response = await client.put(
            f"/api/v1/tasks/{test_task['id']}",
            json={
                "name": "Updated Name",
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_update_task_as_slave_forbidden(
        self, client, test_slave, test_slave_email, test_slave_password, test_task
    ):
        """Test slave cannot update task (403)."""
        # Login as slave
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Try to update
        response = await client.put(
            f"/api/v1/tasks/{test_task['id']}",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403


class TestDeleteTask:
    """Test DELETE /api/v1/tasks/{id} endpoint."""

    async def test_delete_task_as_master(
        self, client, test_master, test_master_email, test_master_password, test_org, test_project
    ):
        """Test master can delete task."""
        # Create task via repository
        task = await task_repo.create(
            name="To Delete",
            description=None,
            project_id=test_project["id"]
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_master_email,
            "password": test_master_password
        })
        token = login_response.json()["access_token"]

        # Delete
        response = await client.delete(
            f"/api/v1/tasks/{task['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify soft deleted via repository
        fetched = await task_repo.get_by_id(task["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is False

        # Cleanup
        await task_repo.delete(task["id"])

    async def test_delete_task_as_slave_forbidden(
        self, client, test_slave, test_slave_email, test_slave_password, test_task
    ):
        """Test slave cannot delete task (403)."""
        # Login as slave
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        token = login_response.json()["access_token"]

        # Try to delete
        response = await client.delete(
            f"/api/v1/tasks/{test_task['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
