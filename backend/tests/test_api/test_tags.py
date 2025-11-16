"""API integration tests for tag endpoints."""

import pytest

from app.repositories.tag_repo import tag_repo


class TestCreateTag:
    """Test POST /api/v1/tags endpoint."""

    async def test_create_tag_as_boss(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test boss can create tag."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        response = await client.post(
            "/api/v1/tags",
            json={"name": "Development"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Development"
        assert data["organization_id"] == str(test_boss["organization_id"])

    async def test_create_tag_as_worker_forbidden(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test worker cannot create tag (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to create tag
        response = await client.post(
            "/api/v1/tags",
            json={"name": "Bug Fix"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    async def test_create_tag_duplicate_name_returns_409(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test creating duplicate tag name returns 409."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        await client.post(
            "/api/v1/tags",
            json={"name": "Duplicate"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to create duplicate
        response = await client.post(
            "/api/v1/tags",
            json={"name": "Duplicate"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_create_tag_unauthenticated_returns_403(self, client):
        """Test creating tag without auth returns 403."""
        response = await client.post(
            "/api/v1/tags",
            json={"name": "Test"}
        )

        assert response.status_code == 403


class TestListTags:
    """Test GET /api/v1/tags endpoint."""

    async def test_list_tags_as_boss(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test boss can list tags."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tags
        tag1 = await tag_repo.create("Client-A", str(test_boss["organization_id"]))
        tag2 = await tag_repo.create("Client-B", str(test_boss["organization_id"]))

        # List tags
        response = await client.get(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

        tag_ids = {t["id"] for t in data["items"]}
        assert str(tag1["id"]) in tag_ids
        assert str(tag2["id"]) in tag_ids

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_boss["organization_id"]))

    async def test_list_tags_as_worker(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test worker can list tags."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # List tags
        response = await client.get(
            "/api/v1/tags",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_list_tags_pagination(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test tag list pagination."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tags
        tags = []
        for i in range(5):
            tag = await tag_repo.create(f"Tag-{i}", str(test_boss["organization_id"]))
            tags.append(tag)

        # List with limit
        response = await client.get(
            "/api/v1/tags?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Cleanup
        for tag in tags:
            await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))


class TestGetTag:
    """Test GET /api/v1/tags/{id} endpoint."""

    async def test_get_tag_as_boss(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test boss can get tag by ID."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("GetTest", str(test_boss["organization_id"]))

        # Get tag
        response = await client.get(
            f"/api/v1/tags/{tag['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(tag["id"])
        assert data["name"] == "GetTest"

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_get_tag_as_worker(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test worker can get tag by ID."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("WorkerGetTest", str(test_worker["organization_id"]))

        # Get tag
        response = await client.get(
            f"/api/v1/tags/{tag['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(tag["id"])

        await tag_repo.delete(str(tag["id"]), str(test_worker["organization_id"]))

    async def test_get_tag_not_found_returns_404(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test getting non-existent tag returns 404."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Get non-existent tag
        response = await client.get(
            "/api/v1/tags/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestUpdateTag:
    """Test PUT /api/v1/tags/{id} endpoint."""

    async def test_update_tag_as_boss(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test boss can update tag."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("OldName", str(test_boss["organization_id"]))

        # Update tag
        response = await client.put(
            f"/api/v1/tags/{tag['id']}",
            json={"name": "NewName"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NewName"
        assert data["id"] == str(tag["id"])

        await tag_repo.delete(str(tag["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_as_worker_forbidden(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test worker cannot update tag (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("TestTag", str(test_worker["organization_id"]))

        # Try to update
        response = await client.put(
            f"/api/v1/tags/{tag['id']}",
            json={"name": "NewName"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        await tag_repo.delete(str(tag["id"]), str(test_worker["organization_id"]))

    async def test_update_tag_duplicate_name_returns_409(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test updating to existing name returns 409."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tags
        tag1 = await tag_repo.create("Tag1", str(test_boss["organization_id"]))
        tag2 = await tag_repo.create("Tag2", str(test_boss["organization_id"]))

        # Try to update tag2 to tag1's name
        response = await client.put(
            f"/api/v1/tags/{tag2['id']}",
            json={"name": "Tag1"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 409

        await tag_repo.delete(str(tag1["id"]), str(test_boss["organization_id"]))
        await tag_repo.delete(str(tag2["id"]), str(test_boss["organization_id"]))

    async def test_update_tag_not_found_returns_404(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test updating non-existent tag returns 404."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Update non-existent tag
        response = await client.put(
            "/api/v1/tags/00000000-0000-0000-0000-000000000000",
            json={"name": "NewName"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestDeleteTag:
    """Test DELETE /api/v1/tags/{id} endpoint."""

    async def test_delete_tag_as_boss(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test boss can delete tag."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("ToDelete", str(test_boss["organization_id"]))

        # Delete tag
        response = await client.delete(
            f"/api/v1/tags/{tag['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify deleted
        result = await tag_repo.get_by_id(str(tag["id"]), str(test_boss["organization_id"]))
        assert result is None

    async def test_delete_tag_as_worker_forbidden(
        self, client, test_worker, test_worker_email, test_worker_password
    ):
        """Test worker cannot delete tag (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("ToDelete", str(test_worker["organization_id"]))

        # Try to delete
        response = await client.delete(
            f"/api/v1/tags/{tag['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

        await tag_repo.delete(str(tag["id"]), str(test_worker["organization_id"]))

    async def test_delete_tag_not_found_returns_404(
        self, client, test_boss, test_boss_email, test_boss_password
    ):
        """Test deleting non-existent tag returns 404."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Delete non-existent tag
        response = await client.delete(
            "/api/v1/tags/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    async def test_delete_tag_cascade_removes_from_time_entries(
        self, client, test_boss, test_boss_email, test_boss_password, test_project
    ):
        """Test deleting tag removes it from time entries (cascade)."""
        from app.repositories.time_entry_repo import time_entry_repo
        from datetime import datetime, timezone

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        token = login_response.json()["access_token"]

        # Create tag
        tag = await tag_repo.create("CascadeTest", str(test_boss["organization_id"]))

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
        response = await client.delete(
            f"/api/v1/tags/{tag['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify tag removed from entry
        updated_entry = await time_entry_repo.get_by_id(
            str(entry["id"]),
            str(test_boss["organization_id"])
        )
        assert updated_entry["tags"] == []

        await time_entry_repo.delete(str(entry["id"]), str(test_boss["organization_id"]))
