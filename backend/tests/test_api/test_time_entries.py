"""
API integration tests for time entry endpoints.

Tests full HTTP request/response cycle for time tracking operations.
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.time_entry_repo import time_entry_repo
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


class TestStartTimer:
    """Test POST /api/v1/time-entries/start endpoint."""

    async def test_start_timer_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test starting timer successfully."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Start timer
        response = await client.post(
            "/api/v1/time-entries/start",
            json={
                "project_id": str(test_project["id"]),
                "task_id": None,
                "is_billable": True,
                "description": "Working on feature"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == str(test_project["id"])
        assert data["is_running"] is True
        assert data["end_time"] is None
        assert data["description"] == "Working on feature"

    async def test_start_timer_with_task(
        self, client, test_worker, test_worker_email, test_worker_password, test_project, test_task
    ):
        """Test starting timer with task."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Start timer
        response = await client.post(
            "/api/v1/time-entries/start",
            json={
                "project_id": str(test_project["id"]),
                "task_id": str(test_task["id"]),
                "is_billable": False,
                "description": None
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(test_task["id"])
        assert data["task_name"] == "Test Task"
        assert data["is_billable"] is False

    async def test_start_timer_already_running(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test starting timer when already running (409)."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Start first timer
        await client.post(
            "/api/v1/time-entries/start",
            json={
                "project_id": str(test_project["id"]),
                "is_billable": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to start second timer
        response = await client.post(
            "/api/v1/time-entries/start",
            json={
                "project_id": str(test_project["id"]),
                "is_billable": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 409
        assert "already have a running timer" in response.json()["detail"]


class TestStopTimer:
    """Test POST /api/v1/time-entries/{id}/stop endpoint."""

    async def test_stop_timer_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test stopping timer successfully."""
        # Create running timer
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Stop timer
        response = await client.post(
            f"/api/v1/time-entries/{entry['id']}/stop",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is False
        assert data["end_time"] is not None
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] > 0

    async def test_stop_timer_not_owner(
        self, client, test_worker, test_worker_email, test_worker_password, test_boss, test_project
    ):
        """Test worker cannot stop boss's timer (403)."""
        # Create timer for boss
        entry = await time_entry_repo.create(
            user_id=str(test_boss["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_boss["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to stop boss's timer
        response = await client.post(
            f"/api/v1/time-entries/{entry['id']}/stop",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])


class TestGetRunningTimer:
    """Test GET /api/v1/time-entries/running endpoint."""

    async def test_get_running_timer_exists(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test getting running timer when it exists."""
        # Create running timer
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Running"
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Get running timer
        response = await client.get(
            "/api/v1/time-entries/running",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(entry["id"])
        assert data["is_running"] is True

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_get_running_timer_not_exists(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test getting running timer when none exists (returns null)."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Get running timer
        response = await client.get(
            "/api/v1/time-entries/running",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        assert response.json() is None


class TestCreateManualEntry:
    """Test POST /api/v1/time-entries endpoint."""

    async def test_create_manual_entry_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test creating manual entry successfully."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create manual entry
        start_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        end_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        response = await client.post(
            "/api/v1/time-entries",
            json={
                "project_id": str(test_project["id"]),
                "task_id": None,
                "start_time": start_time,
                "end_time": end_time,
                "is_billable": True,
                "description": "Forgot to track"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_running"] is False
        assert data["duration_seconds"] is not None
        assert data["description"] == "Forgot to track"

    async def test_create_manual_entry_overlap_blocked(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test manual entry blocked by overlap (400)."""
        # Create existing entry
        await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            is_running=False,
            is_billable=True,
            description=None
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to create overlapping entry
        response = await client.post(
            "/api/v1/time-entries",
            json={
                "project_id": str(test_project["id"]),
                "start_time": "2025-01-15T10:00:00Z",
                "end_time": "2025-01-15T12:00:00Z",
                "is_billable": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "overlap" in response.json()["detail"].lower()


class TestListTimeEntries:
    """Test GET /api/v1/time-entries endpoint."""

    async def test_list_entries_as_worker(
        self, client, test_worker, test_worker_email, test_worker_password, test_boss, test_project
    ):
        """Test worker only sees own entries."""
        # Create entry for worker
        worker_entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Slave entry"
        )

        # Create entry for boss
        boss_entry = await time_entry_repo.create(
            user_id=str(test_boss["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_boss["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Bossentry"
        )

        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # List entries
        response = await client.get(
            "/api/v1/time-entries",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["user_id"] == str(test_worker["id"])

        await time_entry_repo.delete(worker_entry["id"], test_worker["organization_id"])
        await time_entry_repo.delete(boss_entry["id"], test_boss["organization_id"])

    async def test_list_entries_as_boss(
        self, client, test_worker, test_boss, test_boss_email, test_boss_password, test_project
    ):
        """Test boss sees all entries in org."""
        # Create entry for worker
        worker_entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as boss
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # List entries
        response = await client.get(
            "/api/v1/time-entries",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        await time_entry_repo.delete(worker_entry["id"], test_worker["organization_id"])

    async def test_list_entries_with_filters(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test filtering by project, billable, running status."""
        # Create billable entry
        billable = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=True,
            description="Billable"
        )

        # Create non-billable entry
        non_billable = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=False,
            description="Non-billable"
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Filter by billable=true
        response = await client.get(
            "/api/v1/time-entries?is_billable=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_billable"] is True

        await time_entry_repo.delete(billable["id"], test_worker["organization_id"])
        await time_entry_repo.delete(non_billable["id"], test_worker["organization_id"])

    async def test_boss_can_filter_by_user(
        self, client, test_worker, test_boss, test_boss_email, test_boss_password, test_project
    ):
        """Test boss can filter by user_id."""
        # Create entry for worker
        worker_entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as boss
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Filter by worker's user_id
        response = await client.get(
            f"/api/v1/time-entries?user_id={test_worker['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(item["user_id"] == str(test_worker["id"]) for item in data["items"])

        await time_entry_repo.delete(worker_entry["id"], test_worker["organization_id"])


class TestGetTimeEntry:
    """Test GET /api/v1/time-entries/{id} endpoint."""

    async def test_get_time_entry_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test getting time entry by ID."""
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Test entry"
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Get entry
        response = await client.get(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(entry["id"])
        assert data["description"] == "Test entry"

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_worker_cannot_get_other_entry(
        self, client, test_worker, test_worker_email, test_worker_password, test_boss, test_project
    ):
        """Test worker cannot view another user's entry (403)."""
        # Create entry for boss
        entry = await time_entry_repo.create(
            user_id=str(test_boss["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_boss["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to get boss's entry
        response = await client.get(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])


class TestUpdateTimeEntry:
    """Test PUT /api/v1/time-entries/{id} endpoint."""

    async def test_update_time_entry_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test updating time entry successfully."""
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=True,
            description="Original"
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Update entry
        response = await client.put(
            f"/api/v1/time-entries/{entry['id']}",
            json={"description": "Updated", "is_billable": False},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated"
        assert data["is_billable"] is False

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_boss_can_update_any_entry(
        self, client, test_worker, test_boss, test_boss_email, test_boss_password, test_project
    ):
        """Test boss can update any entry in org."""
        # Create entry for worker
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=True,
            description=None
        )

        # Login as boss
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Update worker's entry
        response = await client.put(
            f"/api/v1/time-entries/{entry['id']}",
            json={"description": "Corrected"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Corrected"

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])


class TestDeleteTimeEntry:
    """Test DELETE /api/v1/time-entries/{id} endpoint."""

    async def test_delete_time_entry_success(
        self, client, test_worker, test_worker_email, test_worker_password, test_project
    ):
        """Test deleting time entry successfully."""
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Delete entry
        response = await client.delete(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

    async def test_worker_cannot_delete_other_entry(
        self, client, test_worker, test_worker_email, test_worker_password, test_boss, test_project
    ):
        """Test worker cannot delete another user's entry (403)."""
        # Create entry for boss
        entry = await time_entry_repo.create(
            user_id=str(test_boss["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_boss["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to delete boss's entry
        response = await client.delete(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])

    async def test_boss_can_delete_any_entry(
        self, client, test_worker, test_boss, test_boss_email, test_boss_password, test_project
    ):
        """Test boss can delete any entry in org."""
        # Create entry for worker
        entry = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Login as boss
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Delete worker's entry
        response = await client.delete(
            f"/api/v1/time-entries/{entry['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204
