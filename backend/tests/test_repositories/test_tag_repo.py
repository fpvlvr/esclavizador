"""Tests for TagRepository."""

import pytest
from tortoise.exceptions import IntegrityError

from app.repositories.tag_repo import tag_repo


class TestTagRepository:
    """Test TagRepository methods."""

    async def test_create_tag(self, test_org):
        """Test creating a tag."""
        tag = await tag_repo.create(
            name="Bug Fix",
            org_id=str(test_org["id"])
        )

        assert tag["id"] is not None
        assert tag["name"] == "Bug Fix"
        assert tag["organization_id"] == test_org["id"]
        assert tag["created_at"] is not None

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_create_duplicate_tag_raises_integrity_error(self, test_org):
        """Test creating duplicate tag name in same org raises IntegrityError."""
        tag1 = await tag_repo.create(name="Development", org_id=str(test_org["id"]))

        with pytest.raises(IntegrityError):
            await tag_repo.create(name="Development", org_id=str(test_org["id"]))

        await tag_repo.delete(str(tag1["id"]), str(test_org["id"]))

    async def test_get_by_id_success(self, test_org):
        """Test getting tag by ID."""
        created_tag = await tag_repo.create(
            name="Testing",
            org_id=str(test_org["id"])
        )

        tag = await tag_repo.get_by_id(str(created_tag["id"]), str(test_org["id"]))

        assert tag is not None
        assert tag["id"] == created_tag["id"]
        assert tag["name"] == "Testing"

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_get_by_id_wrong_org_returns_none(self, test_org):
        """Test getting tag from wrong org returns None."""
        tag = await tag_repo.create(name="Meeting", org_id=str(test_org["id"]))

        result = await tag_repo.get_by_id(str(tag["id"]), "00000000-0000-0000-0000-000000000000")

        assert result is None

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_get_by_name_case_insensitive(self, test_org):
        """Test getting tag by name (case-insensitive)."""
        tag = await tag_repo.create(name="Feature", org_id=str(test_org["id"]))

        # Test exact match
        result1 = await tag_repo.get_by_name("Feature", str(test_org["id"]))
        assert result1 is not None
        assert result1["id"] == tag["id"]

        # Test case-insensitive match
        result2 = await tag_repo.get_by_name("FEATURE", str(test_org["id"]))
        assert result2 is not None
        assert result2["id"] == tag["id"]

        result3 = await tag_repo.get_by_name("feature", str(test_org["id"]))
        assert result3 is not None
        assert result3["id"] == tag["id"]

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_get_by_name_not_found(self, test_org):
        """Test getting non-existent tag by name returns None."""
        result = await tag_repo.get_by_name("NonExistent", str(test_org["id"]))
        assert result is None

    async def test_list_tags(self, test_org):
        """Test listing tags with pagination."""
        tag1 = await tag_repo.create(name="Client-A", org_id=str(test_org["id"]))
        tag2 = await tag_repo.create(name="Client-B", org_id=str(test_org["id"]))

        result = await tag_repo.list(test_org["id"], {}, limit=50, offset=0)

        assert result["total"] >= 2
        assert len(result["items"]) >= 2

        tag_ids = {str(t["id"]) for t in result["items"]}
        assert str(tag1["id"]) in tag_ids
        assert str(tag2["id"]) in tag_ids

        await tag_repo.delete(str(tag1["id"]), str(test_org["id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_org["id"]))

    async def test_list_tags_pagination(self, test_org):
        """Test tag list pagination."""
        tags = []
        for i in range(5):
            tag = await tag_repo.create(name=f"Tag-{i}", org_id=str(test_org["id"]))
            tags.append(tag)

        result = await tag_repo.list(test_org["id"], {}, limit=2, offset=0)
        assert len(result["items"]) == 2
        assert result["total"] >= 5

        result2 = await tag_repo.list(test_org["id"], {}, limit=2, offset=2)
        assert len(result2["items"]) == 2

        for tag in tags:
            await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_update_tag(self, test_org):
        """Test updating tag name."""
        tag = await tag_repo.create(name="OldName", org_id=str(test_org["id"]))

        updated = await tag_repo.update(
            str(tag["id"]),
            test_org["id"],
            {"name": "NewName"}
        )

        assert updated is not None
        assert updated["name"] == "NewName"
        assert updated["id"] == tag["id"]

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_update_tag_wrong_org_returns_none(self, test_org):
        """Test updating tag from wrong org returns None."""
        tag = await tag_repo.create(name="TestTag", org_id=str(test_org["id"]))

        result = await tag_repo.update(
            str(tag["id"]),
            "00000000-0000-0000-0000-000000000000",
            {"name": "NewName"}
        )

        assert result is None

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_update_to_duplicate_name_raises_integrity_error(self, test_org):
        """Test updating tag to existing name raises IntegrityError."""
        tag1 = await tag_repo.create(name="Tag1", org_id=str(test_org["id"]))
        tag2 = await tag_repo.create(name="Tag2", org_id=str(test_org["id"]))

        with pytest.raises(IntegrityError):
            await tag_repo.update(
                str(tag2["id"]),
                test_org["id"],
                {"name": "Tag1"}
            )

        await tag_repo.delete(str(tag1["id"]), str(test_org["id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_org["id"]))

    async def test_delete_tag(self, test_org):
        """Test deleting tag."""
        tag = await tag_repo.create(name="ToDelete", org_id=str(test_org["id"]))

        deleted = await tag_repo.delete(str(tag["id"]), str(test_org["id"]))
        assert deleted is True

        result = await tag_repo.get_by_id(str(tag["id"]), str(test_org["id"]))
        assert result is None

    async def test_delete_tag_wrong_org_returns_false(self, test_org):
        """Test deleting tag from wrong org returns False."""
        tag = await tag_repo.create(name="TestTag", org_id=str(test_org["id"]))

        result = await tag_repo.delete(
            str(tag["id"]),
            "00000000-0000-0000-0000-000000000000"
        )

        assert result is False

        await tag_repo.delete(str(tag["id"]), str(test_org["id"]))

    async def test_delete_nonexistent_tag_returns_false(self, test_org):
        """Test deleting non-existent tag returns False."""
        result = await tag_repo.delete(
            "00000000-0000-0000-0000-000000000000",
            str(test_org["id"])
        )
        assert result is False
