"""
Repository tests for time entry data access.

Tests TimeEntry repository layer (ORM → TypedDict conversion).
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.time_entry_repo import time_entry_repo
from app.repositories.project_repo import project_repo
from app.repositories.task_repo import task_repo


class TestCreateTimeEntry:
    """Test time_entry_repo.create()."""

    async def test_create_time_entry_with_task(self, test_org, test_slave, test_project, test_task):
        """Test creating time entry with all fields."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc)

        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=str(test_task["id"]),
            organization_id=str(test_org["id"]),
            start_time=start_time,
            end_time=end_time,
            is_running=False,
            is_billable=True,
            description="Test entry"
        )

        assert entry["user_id"] == test_slave["id"]
        assert entry["project_id"] == test_project["id"]
        assert entry["task_id"] == test_task["id"]
        assert entry["is_running"] is False
        assert entry["is_billable"] is True
        assert entry["description"] == "Test entry"
        assert entry["user_email"] == test_slave["email"]
        assert entry["project_name"] == "Test Project"
        assert entry["task_name"] == "Test Task"
        assert entry["duration_seconds"] is not None
        assert entry["duration_seconds"] > 0

        await time_entry_repo.delete(entry["id"], test_org["id"])

    async def test_create_time_entry_without_task(self, test_org, test_slave, test_project):
        """Test creating time entry without task (project-level tracking)."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=False,
            description=None
        )

        assert entry["task_id"] is None
        assert entry["task_name"] is None
        assert entry["is_running"] is True
        assert entry["duration_seconds"] is None

        await time_entry_repo.delete(entry["id"], test_org["id"])

    async def test_create_running_timer(self, test_org, test_slave, test_project):
        """Test creating running timer (no end_time)."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Running timer"
        )

        assert entry["is_running"] is True
        assert entry["end_time"] is None
        assert entry["duration_seconds"] is None

        await time_entry_repo.delete(entry["id"], test_org["id"])


class TestGetRunningEntry:
    """Test time_entry_repo.get_running_entry()."""

    async def test_get_running_entry_exists(self, test_org, test_slave, test_project):
        """Test getting running entry when it exists."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        running = await time_entry_repo.get_running_entry(test_slave["id"], test_org["id"])

        assert running is not None
        assert running["id"] == entry["id"]
        assert running["is_running"] is True

        await time_entry_repo.delete(entry["id"], test_org["id"])

    async def test_get_running_entry_not_exists(self, test_org, test_slave):
        """Test getting running entry when none exists."""
        running = await time_entry_repo.get_running_entry(test_slave["id"], test_org["id"])
        assert running is None


class TestStopTimer:
    """Test time_entry_repo.stop_timer()."""

    async def test_stop_timer(self, test_org, test_slave, test_project):
        """Test stopping a running timer."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=start_time,
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        end_time = datetime.now(timezone.utc)
        stopped = await time_entry_repo.stop_timer(str(entry["id"]), end_time)

        assert stopped["is_running"] is False
        assert stopped["end_time"] == end_time
        assert stopped["duration_seconds"] is not None
        assert stopped["duration_seconds"] > 0

        await time_entry_repo.delete(entry["id"], test_org["id"])


class TestCheckOverlap:
    """Test time_entry_repo.check_overlap()."""

    async def test_overlap_with_completed_entry(self, test_org, test_slave, test_project):
        """Test overlap detection with completed entry."""
        # Create existing entry: 9am-11am
        existing_start = datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        existing_end = datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=existing_start,
            end_time=existing_end,
            is_running=False,
            is_billable=True,
            description=None
        )

        # Test overlap: 10am-12pm (overlaps 10am-11am)
        has_overlap = await time_entry_repo.check_overlap(
            user_id=str(test_slave["id"]),
            start_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        )

        assert has_overlap is True

    async def test_no_overlap_with_completed_entry(self, test_org, test_slave, test_project):
        """Test no overlap with completed entry."""
        # Create existing entry: 9am-11am
        existing_start = datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        existing_end = datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=existing_start,
            end_time=existing_end,
            is_running=False,
            is_billable=True,
            description=None
        )

        # Test no overlap: 11am-1pm (after existing)
        has_overlap = await time_entry_repo.check_overlap(
            user_id=str(test_slave["id"]),
            start_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
        )

        assert has_overlap is False

    async def test_overlap_with_running_timer(self, test_org, test_slave, test_project):
        """Test overlap detection with running timer."""
        # Create running timer starting at 9am
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # Test overlap: 10am-11am (overlaps with running timer)
        has_overlap = await time_entry_repo.check_overlap(
            user_id=str(test_slave["id"]),
            start_time=datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
        )

        assert has_overlap is True

    async def test_exclude_entry_from_overlap_check(self, test_org, test_slave, test_project):
        """Test excluding specific entry from overlap check (for updates)."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            is_running=False,
            is_billable=True,
            description=None
        )

        # Check overlap excluding the entry itself (should not overlap)
        has_overlap = await time_entry_repo.check_overlap(
            user_id=str(test_slave["id"]),
            start_time=datetime(2025, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2025, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            exclude_entry_id=str(entry["id"])
        )

        assert has_overlap is False

        await time_entry_repo.delete(entry["id"], test_org["id"])


class TestListTimeEntries:
    """Test time_entry_repo.list()."""

    async def test_list_with_filters(self, test_org, test_slave, test_master, test_project):
        """Test listing with various filters."""
        # Create entries for slave
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=True,
            description="Billable"
        )
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            is_running=False,
            is_billable=False,
            description="Non-billable"
        )

        # Filter by billable
        result = await time_entry_repo.list(
            org_id=test_org["id"],
            filters={"is_billable": True},
            limit=50,
            offset=0
        )

        assert result["total"] == 1
        assert result["items"][0]["is_billable"] is True

    async def test_list_respects_org_isolation(self, test_org, test_slave, test_project, second_org):
        """Test that list only returns entries from specified org."""
        # Create entry in test_org
        await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        # List from second_org (should be empty)
        result = await time_entry_repo.list(
            org_id=second_org["id"],
            filters={},
            limit=50,
            offset=0
        )

        assert result["total"] == 0


class TestUpdateTimeEntry:
    """Test time_entry_repo.update()."""

    async def test_update_time_entry(self, test_org, test_slave, test_project):
        """Test updating time entry fields."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description="Original"
        )

        updated = await time_entry_repo.update(
            entry_id=str(entry["id"]),
            org_id=test_org["id"],
            data={"description": "Updated", "is_billable": False}
        )

        assert updated["description"] == "Updated"
        assert updated["is_billable"] is False

        await time_entry_repo.delete(entry["id"], test_org["id"])


class TestDeleteTimeEntry:
    """Test time_entry_repo.delete()."""

    async def test_delete_time_entry(self, test_org, test_slave, test_project):
        """Test hard deleting time entry."""
        entry = await time_entry_repo.create(
            user_id=str(test_slave["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_org["id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None
        )

        deleted = await time_entry_repo.delete(str(entry["id"]), test_org["id"])
        assert deleted is True

        # Verify it's gone
        retrieved = await time_entry_repo.get_by_id(str(entry["id"]), test_org["id"])
        assert retrieved is None
