"""Service tests for tag business logic."""

import pytest
from fastapi import HTTPException

from app.services.tag_service import tag_service
from app.schemas.tag import TagCreate, TagUpdate
from app.repositories.tag_repo import tag_repo


class TestCreateTag:
    """Test tag_service.create_tag()."""

    async def test_create_tag_success(self, test_boss):
        """Test creating tag successfully."""
        data = TagCreate(name="Development")

        tag = await tag_service.create_tag(test_boss, data)

        assert tag["name"] == "Development"
        assert tag["organization_id"] == test_boss["organization_id"]

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_create_tag_strips_whitespace(self, test_boss):
        """Test that tag name is stripped."""
        data = TagCreate(name="  Bug Fix  ")

        tag = await tag_service.create_tag(test_boss, data)

        assert tag["name"] == "Bug Fix"

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_create_tag_duplicate_name_raises_409(self, test_boss):
        """Test creating duplicate tag name raises 409 Conflict."""
        data1 = TagCreate(name="Testing")
        tag1 = await tag_service.create_tag(test_boss, data1)

        # Try to create duplicate
        data2 = TagCreate(name="Testing")
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.create_tag(test_boss, data2)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))

    async def test_create_tag_case_insensitive_duplicate_raises_409(self, test_boss):
        """Test case-insensitive duplicate detection."""
        data1 = TagCreate(name="Feature")
        tag1 = await tag_service.create_tag(test_boss, data1)

        # Try to create with different case
        data2 = TagCreate(name="FEATURE")
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.create_tag(test_boss, data2)

        assert exc_info.value.status_code == 409

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))

    async def test_create_tag_empty_name_after_strip_raises_400(self, test_boss):
        """Test that empty name after stripping raises 400."""
        data = TagCreate(name="   ")

        with pytest.raises(HTTPException) as exc_info:
            await tag_service.create_tag(test_boss, data)

        assert exc_info.value.status_code == 400
        assert "1-100 characters" in exc_info.value.detail


class TestListTags:
    """Test tag_service.list_tags()."""

    async def test_list_tags_success(self, test_boss):
        """Test listing tags with pagination."""
        # Create tags
        tag1 = await tag_repo.create("Client-A", str(test_boss["organization_id"]))
        tag2 = await tag_repo.create("Client-B", str(test_boss["organization_id"]))

        result = await tag_service.list_tags(test_boss, limit=50, offset=0)

        assert result["total"] >= 2
        assert result["limit"] == 50
        assert result["offset"] == 0

        tag_ids = {str(t["id"]) for t in result["items"]}
        assert str(tag1["id"]) in tag_ids
        assert str(tag2["id"]) in tag_ids

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_boss["organization_id"]))

    async def test_list_tags_pagination(self, test_boss):
        """Test tag list pagination."""
        tags = []
        for i in range(5):
            tag = await tag_repo.create(f"Tag-{i}", str(test_boss["organization_id"]))
            tags.append(tag)

        result = await tag_service.list_tags(test_boss, limit=2, offset=0)
        assert len(result["items"]) == 2

        result2 = await tag_service.list_tags(test_boss, limit=2, offset=2)
        assert len(result2["items"]) == 2

        for tag in tags:
            await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))


class TestGetTag:
    """Test tag_service.get_tag()."""

    async def test_get_tag_success(self, test_boss):
        """Test getting tag by ID."""
        tag = await tag_repo.create("GetTest", str(test_boss["organization_id"]))

        result = await tag_service.get_tag(test_boss, str(tag["id"]))

        assert result["id"] == tag["id"]
        assert result["name"] == "GetTest"

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_get_tag_not_found_raises_404(self, test_boss):
        """Test getting non-existent tag raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.get_tag(test_boss, "00000000-0000-0000-0000-000000000000")

        assert exc_info.value.status_code == 404


class TestUpdateTag:
    """Test tag_service.update_tag()."""

    async def test_update_tag_success(self, test_boss):
        """Test updating tag name."""
        tag = await tag_repo.create("OldName", str(test_boss["organization_id"]))

        data = TagUpdate(name="NewName")
        updated = await tag_service.update_tag(test_boss, str(tag["id"]), data)

        assert updated["name"] == "NewName"
        assert updated["id"] == tag["id"]

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_strips_whitespace(self, test_boss):
        """Test that updated name is stripped."""
        tag = await tag_repo.create("OldName", str(test_boss["organization_id"]))

        data = TagUpdate(name="  NewName  ")
        updated = await tag_service.update_tag(test_boss, str(tag["id"]), data)

        assert updated["name"] == "NewName"

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_not_found_raises_404(self, test_boss):
        """Test updating non-existent tag raises 404."""
        data = TagUpdate(name="NewName")

        with pytest.raises(HTTPException) as exc_info:
            await tag_service.update_tag(
                test_boss,
                "00000000-0000-0000-0000-000000000000",
                data
            )

        assert exc_info.value.status_code == 404

    async def test_update_tag_duplicate_name_raises_409(self, test_boss):
        """Test updating to existing name raises 409."""
        tag1 = await tag_repo.create("Tag1", str(test_boss["organization_id"]))
        tag2 = await tag_repo.create("Tag2", str(test_boss["organization_id"]))

        data = TagUpdate(name="Tag1")
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.update_tag(test_boss, str(tag2["id"]), data)

        assert exc_info.value.status_code == 409

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_case_insensitive_duplicate_raises_409(self, test_boss):
        """Test case-insensitive duplicate detection on update."""
        tag1 = await tag_repo.create("Feature", str(test_boss["organization_id"]))
        tag2 = await tag_repo.create("BugFix", str(test_boss["organization_id"]))

        data = TagUpdate(name="FEATURE")
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.update_tag(test_boss, str(tag2["id"]), data)

        assert exc_info.value.status_code == 409

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_to_same_name_succeeds(self, test_boss):
        """Test updating tag to its own name (different case) succeeds."""
        tag = await tag_repo.create("MyTag", str(test_boss["organization_id"]))

        data = TagUpdate(name="MYTAG")
        updated = await tag_service.update_tag(test_boss, str(tag["id"]), data)

        assert updated["name"] == "MYTAG"

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_empty_name_raises_400(self, test_boss):
        """Test updating to empty name raises 400."""
        tag = await tag_repo.create("MyTag", str(test_boss["organization_id"]))

        data = TagUpdate(name="   ")
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.update_tag(test_boss, str(tag["id"]), data)

        assert exc_info.value.status_code == 400

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))


class TestDeleteTag:
    """Test tag_service.delete_tag()."""

    async def test_delete_tag_success(self, test_boss):
        """Test deleting tag."""
        tag = await tag_repo.create("ToDelete", str(test_boss["organization_id"]))

        await tag_service.delete_tag(test_boss, str(tag["id"]))

        result = await tag_repo.get_by_id(str(tag["id"]), str(test_boss["organization_id"]))
        assert result is None

    async def test_delete_tag_not_found_raises_404(self, test_boss):
        """Test deleting non-existent tag raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            await tag_service.delete_tag(
                test_boss,
                "00000000-0000-0000-0000-000000000000"
            )

        assert exc_info.value.status_code == 404

    async def test_delete_tag_removes_from_time_entries(self, test_boss, test_project):
        """Test that deleting tag removes it from time entries (cascade)."""
        from app.repositories.time_entry_repo import time_entry_repo
        from datetime import datetime, timezone

        # Create tag
        tag = await tag_repo.create("ToDelete", str(test_boss["organization_id"]))

        # Create time entry with tag
        entry = await time_entry_repo.create(
            user_id=str(test_boss["id"]),
            project_id=str(test_project["id"]),
            task_id=None,
            organization_id=str(test_boss["organization_id"]),
            start_time=datetime.now(timezone.utc),
            end_time=None,
            is_running=True,
            is_billable=True,
            description=None,
            tag_ids=[str(tag["id"])]
        )

        # Delete tag
        await tag_service.delete_tag(test_boss, str(tag["id"]))

        # Verify tag is removed from entry
        updated_entry = await time_entry_repo.get_by_id(
            str(entry["id"]),
            str(test_boss["organization_id"])
        )
        assert updated_entry["tags"] == []

        await time_entry_repo.delete(str(entry["id"]), str(test_boss["organization_id"]))
