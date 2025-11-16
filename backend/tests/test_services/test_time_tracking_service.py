"""
Service tests for time tracking business logic.

Tests time tracking service layer (authorization, validation, multi-tenant).
"""

import pytest
from datetime import datetime, timedelta, timezone, date
from uuid import uuid4

from app.services.time_tracking_service import time_tracking_service
from app.schemas.time_entry import TimeEntryStart, TimeEntryCreate, TimeEntryUpdate
from app.repositories.time_entry_repo import time_entry_repo
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


class TestStartTimer:
    """Test time_tracking_service.start_timer()."""

    async def test_start_timer_success(self, test_worker, test_project):
        """Test starting timer successfully."""
        data = TimeEntryStart(
            project_id=test_project["id"],
            task_id=None,
            is_billable=True,
            description="Working on feature"
        )

        entry = await time_tracking_service.start_timer(test_worker, data)

        assert entry["user_id"] == test_worker["id"]
        assert entry["project_id"] == test_project["id"]
        assert entry["is_running"] is True
        assert entry["end_time"] is None

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_start_timer_with_task(self, test_worker, test_project, test_task):
        """Test starting timer with specific task."""
        data = TimeEntryStart(
            project_id=test_project["id"],
            task_id=test_task["id"],
            is_billable=False,
            description=None
        )

        entry = await time_tracking_service.start_timer(test_worker, data)

        assert entry["task_id"] == test_task["id"]
        assert entry["task_name"] == "Test Task"
        assert entry["is_billable"] is False

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_start_timer_already_running(self, test_worker, test_project):
        """Test starting timer when one is already running (409)."""
        data = TimeEntryStart(
            project_id=test_project["id"],
            task_id=None,
            is_billable=True,
            description=None
        )

        # Start first timer
        entry1 = await time_tracking_service.start_timer(test_worker, data)

        # Try to start second timer (should fail)
        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.start_timer(test_worker, data)

        assert exc_info.value.status_code == 409
        assert "already have a running timer" in str(exc_info.value.detail)

        await time_entry_repo.delete(entry1["id"], test_worker["organization_id"])

    async def test_start_timer_invalid_project(self, test_worker):
        """Test starting timer with non-existent project (404)."""
        data = TimeEntryStart(
            project_id=uuid4(),
            task_id=None,
            is_billable=True,
            description=None
        )

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.start_timer(test_worker, data)

        assert exc_info.value.status_code == 404
        assert "Project not found" in str(exc_info.value.detail)

    async def test_start_timer_task_wrong_project(self, test_worker, test_org):
        """Test starting timer with task that doesn't belong to project (404)."""
        # Create two projects and a task in project1
        project1 = await project_repo.create("Project 1", None, test_org["id"])
        project2 = await project_repo.create("Project 2", None, test_org["id"])
        task1 = await task_repo.create("Task 1", None, project1["id"])

        # Try to start timer on project2 with task from project1
        data = TimeEntryStart(
            project_id=project2["id"],
            task_id=task1["id"],
            is_billable=True,
            description=None
        )

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.start_timer(test_worker, data)

        assert exc_info.value.status_code == 404
        assert "doesn't belong to project" in str(exc_info.value.detail)

        await task_repo.delete(task1["id"])
        await project_repo.delete(project1["id"])
        await project_repo.delete(project2["id"])


class TestStopTimer:
    """Test time_tracking_service.stop_timer()."""

    async def test_stop_timer_success(self, test_worker, test_project):
        """Test stopping timer successfully."""
        # Start timer
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

        # Stop it
        stopped = await time_tracking_service.stop_timer(test_worker, str(entry["id"]))

        assert stopped["is_running"] is False
        assert stopped["end_time"] is not None
        assert stopped["duration_seconds"] > 0

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_stop_timer_not_owner(self, test_worker, test_boss, test_project):
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

        # Slave tries to stop it
        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.stop_timer(test_worker, str(entry["id"]))

        assert exc_info.value.status_code == 403
        assert "only stop your own timers" in str(exc_info.value.detail)

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])

    async def test_stop_timer_already_stopped(self, test_worker, test_project):
        """Test stopping already stopped timer (400)."""
        # Create already-stopped entry
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

        # Try to stop it again
        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.stop_timer(test_worker, str(entry["id"]))

        assert exc_info.value.status_code == 400
        assert "already stopped" in str(exc_info.value.detail)

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])


class TestCreateManualEntry:
    """Test time_tracking_service.create_manual_entry()."""

    async def test_create_manual_entry_success(self, test_worker, test_project):
        """Test creating manual entry successfully."""
        data = TimeEntryCreate(
            project_id=test_project["id"],
            task_id=None,
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            is_billable=True,
            description="Forgot to track this"
        )

        entry = await time_tracking_service.create_manual_entry(test_worker, data)

        assert entry["user_id"] == test_worker["id"]
        assert entry["is_running"] is False
        assert entry["duration_seconds"] is not None

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_create_manual_entry_overlap_blocked(self, test_worker, test_project):
        """Test manual entry creation blocked by overlap (400)."""
        # Create existing entry: 9am-11am
        existing = await time_entry_repo.create(
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

        # Try to create overlapping entry: 10am-12pm
        data = TimeEntryCreate(
            project_id=test_project["id"],
            task_id=None,
            start_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            is_billable=True,
            description=None
        )

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.create_manual_entry(test_worker, data)

        assert exc_info.value.status_code == 400
        assert "overlaps" in str(exc_info.value.detail)

        await time_entry_repo.delete(existing["id"], test_worker["organization_id"])

    async def test_create_manual_entry_overlap_with_running_timer(self, test_worker, test_project):
        """Test manual entry blocked by running timer."""
        # Create running timer from 9am
        running = await time_entry_repo.create(
            user_id=str(test_worker["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_worker["organization_id"]),
            start_time=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Try to create manual entry: 10am-11am (overlaps running timer)
        data = TimeEntryCreate(
            project_id=test_project["id"],
            task_id=None,
            start_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            is_billable=True,
            description=None
        )

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.create_manual_entry(test_worker, data)

        assert exc_info.value.status_code == 400
        assert "overlaps" in str(exc_info.value.detail)

        await time_entry_repo.delete(running["id"], test_worker["organization_id"])


class TestListEntries:
    """Test time_tracking_service.list_entries()."""

    async def test_worker_sees_only_own_entries(self, test_worker, test_boss, test_project):
        """Test worker can only see their own entries."""
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

        # Slave lists entries
        result = await time_tracking_service.list_entries(
            user=test_worker,
            project_id=None,
            task_id=None,
            is_billable=None,
            user_id=None,
            start_date=None,
            end_date=None,
            is_running=None,
            tag_ids=None,
            limit=50,
            offset=0
        )

        # Should only see own entry
        assert result["total"] == 1
        assert result["items"][0]["user_id"] == test_worker["id"]

        await time_entry_repo.delete(worker_entry["id"], test_worker["organization_id"])
        await time_entry_repo.delete(boss_entry["id"], test_boss["organization_id"])

    async def test_boss_sees_all_entries(self, test_worker, test_boss, test_project):
        """Test boss can see all entries in org."""
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

        # Bosslists entries
        result = await time_tracking_service.list_entries(
            user=test_boss,
            project_id=None,
            task_id=None,
            is_billable=None,
            user_id=None,
            start_date=None,
            end_date=None,
            is_running=None,
            tag_ids=None,
            limit=50,
            offset=0
        )

        # Should see worker's entry
        assert result["total"] >= 1

        await time_entry_repo.delete(worker_entry["id"], test_worker["organization_id"])

    async def test_worker_cannot_filter_by_other_user(self, test_worker, test_boss):
        """Test worker cannot filter by other user's ID (403)."""
        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.list_entries(
                user=test_worker,
                project_id=None,
                task_id=None,
                is_billable=None,
                user_id=str(test_boss["id"]),
                start_date=None,
                end_date=None,
                is_running=None,
                tag_ids=None,
                limit=50,
                offset=0
            )

        assert exc_info.value.status_code == 403


class TestUpdateEntry:
    """Test time_tracking_service.update_entry()."""

    async def test_update_entry_success(self, test_worker, test_project):
        """Test updating entry successfully."""
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

        data = TimeEntryUpdate(description="Updated", is_billable=False)
        updated = await time_tracking_service.update_entry(test_worker, str(entry["id"]), data)

        assert updated["description"] == "Updated"
        assert updated["is_billable"] is False

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_cannot_update_running_timer_times(self, test_worker, test_project):
        """Test cannot update times of running timer (400)."""
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

        data = TimeEntryUpdate(start_time=datetime.now(timezone.utc) - timedelta(hours=1))

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.update_entry(test_worker, str(entry["id"]), data)

        assert exc_info.value.status_code == 400
        assert "running timer" in str(exc_info.value.detail)

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])

    async def test_worker_cannot_update_other_entry(self, test_worker, test_boss, test_project):
        """Test worker cannot update another user's entry (403)."""
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

        data = TimeEntryUpdate(description="Hacked")

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.update_entry(test_worker, str(entry["id"]), data)

        assert exc_info.value.status_code == 403

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])

    async def test_boss_can_update_any_entry(self, test_worker, test_boss, test_project):
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

        data = TimeEntryUpdate(description="Corrected by boss")
        updated = await time_tracking_service.update_entry(test_boss, str(entry["id"]), data)

        assert updated["description"] == "Corrected by boss"

        await time_entry_repo.delete(entry["id"], test_worker["organization_id"])


class TestDeleteEntry:
    """Test time_tracking_service.delete_entry()."""

    async def test_delete_entry_success(self, test_worker, test_project):
        """Test deleting entry successfully."""
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

        await time_tracking_service.delete_entry(test_worker, str(entry["id"]))

        # Verify it's deleted
        result = await time_entry_repo.get_by_id(str(entry["id"]), test_worker["organization_id"])
        assert result is None

    async def test_worker_cannot_delete_other_entry(self, test_worker, test_boss, test_project):
        """Test worker cannot delete another user's entry (403)."""
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

        with pytest.raises(Exception) as exc_info:
            await time_tracking_service.delete_entry(test_worker, str(entry["id"]))

        assert exc_info.value.status_code == 403

        await time_entry_repo.delete(entry["id"], test_boss["organization_id"])
