"""
API integration tests for project endpoints.

Tests full HTTP request/response cycle including:
- Authentication/authorization
- Request validation
- Business logic
- Multi-tenant isolation
- Response formatting
"""

from app.repositories.project_repo import project_repo

class TestCreateProject:
    """Test POST /api/v1/projects endpoint."""

    async def test_create_project_as_boss(self, client, test_boss, test_boss_email, test_boss_password):
        """Test boss can create project."""
        # Login to get token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_boss_email,
            "password": test_boss_password
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Create project
        response = await client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "Test description"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Project"
        assert data["description"] == "Test description"
        assert data["is_active"] is True
        assert data["task_count"] == 0
        assert "id" in data
        assert "created_at" in data

    async def test_create_project_as_worker_forbidden(self, client, test_worker, test_worker_email, test_worker_password):
        """Test worker cannot create project (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to create project
        response = await client.post(
            "/api/v1/projects",
            json={"name": "New Project"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Boss role required"

    async def test_create_project_no_auth(self, client):
        """Test creating project without auth (401)."""
        response = await client.post(
            "/api/v1/projects",
            json={"name": "New Project"}
        )

        assert response.status_code == 403  # HTTPBearer returns 403 for missing token

    async def test_create_project_validation_error(self, client, test_boss):
        """Test validation errors (422)."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Name too short
        response = await client.post(
            "/api/v1/projects",
            json={"name": "A"},  # Too short (min 2 chars)
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 422


class TestListProjects:
    """Test GET /api/v1/projects endpoint."""

    async def test_list_projects_as_user(self, client, test_worker, test_project, test_worker_email, test_worker_password):
        """Test any user can list projects."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # List projects
        response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["task_count"] == 0

    async def test_list_projects_filter_is_active(self, client, test_worker, test_org, test_worker_email, test_worker_password):
        """Test filtering by is_active."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create active and inactive projects via repository
        active = await project_repo.create(
            name="Active",
            description=None,
            color="#3b82f6",
            org_id=test_org["id"]
        )
        inactive = await project_repo.create(
            name="Inactive",
            description=None,
            color="#10b981",
            org_id=test_org["id"]
        )
        # Soft delete to make inactive
        await project_repo.soft_delete(inactive["id"], test_org["id"])

        # Filter active only
        response = await client.get(
            "/api/v1/projects?is_active=true",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert all(p["is_active"] is True for p in data["items"])

        # Cleanup
        await project_repo.delete(active["id"])
        await project_repo.delete(inactive["id"])

    async def test_list_projects_pagination(self, client, test_worker, test_org, test_worker_email, test_worker_password):
        """Test pagination with limit/offset."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Create multiple projects via repository
        projects = []
        for i in range(5):
            p = await project_repo.create(
                name=f"Project {i}",
                description=None,
                color="#f59e0b",
                org_id=test_org["id"]
            )
            projects.append(p)

        # Get first 2
        response = await client.get(
            "/api/v1/projects?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Cleanup
        for p in projects:
            await project_repo.delete(p["id"])

    async def test_list_projects_multi_tenant_isolation(self, client, test_worker, second_org, test_worker_email, test_worker_password):
        """Test users only see their org's projects."""
        # Create project in second org via repository
        other_project = await project_repo.create(
            name="Other Org Project",
            description=None,
            color="#8b5cf6",
            org_id=second_org["id"]
        )

        # Login as test_worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # List projects
        response = await client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should not see other org's project
        project_names = [p["name"] for p in data["items"]]
        assert "Other Org Project" not in project_names

        # Cleanup
        await project_repo.delete(other_project["id"])


class TestGetProject:
    """Test GET /api/v1/projects/{id} endpoint."""

    async def test_get_project_success(self, client, test_worker, test_project, test_worker_email, test_worker_password):
        """Test getting project by ID."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Get project
        response = await client.get(
            f"/api/v1/projects/{test_project['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project["id"])
        assert data["name"] == "Test Project"
        assert "task_count" in data

    async def test_get_project_not_found(self, client, test_worker, test_worker_email, test_worker_password):
        """Test 404 when project doesn't exist."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Get non-existent project
        response = await client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    async def test_get_project_wrong_org(self, client, test_worker, second_org_project, test_worker_email, test_worker_password):
        """Test 404 when accessing other org's project."""
        # Login as test_worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to get other org's project
        response = await client.get(
            f"/api/v1/projects/{second_org_project['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404  # Returns 404, not 403, to avoid info leakage


class TestUpdateProject:
    """Test PUT /api/v1/projects/{id} endpoint."""

    async def test_update_project_as_boss(self, client, test_boss, test_project):
        """Test boss can update project."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Update project
        response = await client.put(
            f"/api/v1/projects/{test_project['id']}",
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

    async def test_update_project_as_worker_forbidden(self, client, test_worker, test_project, test_worker_email, test_worker_password):
        """Test worker cannot update project (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to update
        response = await client.put(
            f"/api/v1/projects/{test_project['id']}",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    async def test_update_project_partial(self, client, test_boss, test_project):
        """Test partial update."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Update only name
        response = await client.put(
            f"/api/v1/projects/{test_project['id']}",
            json={"name": "Updated Name Only"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name Only"
        assert data["description"] == "Test project description"  # Unchanged

    async def test_update_project_not_found(self, client, test_boss):
        """Test 404 when updating non-existent project."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Update non-existent project
        response = await client.put(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


class TestDeleteProject:
    """Test DELETE /api/v1/projects/{id} endpoint."""

    async def test_delete_project_as_boss(self, client, test_boss, test_org):
        """Test boss can delete project."""
        # Create project via repository
        project = await project_repo.create(
            name="To Delete",
            description=None,
            color="#3b82f6",
            org_id=test_org["id"]
        )

        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Delete
        response = await client.delete(
            f"/api/v1/projects/{project['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify soft deleted via repository
        fetched = await project_repo.get_by_id(project["id"], test_org["id"])
        assert fetched is not None
        assert fetched["is_active"] is False

        # Cleanup
        await project_repo.delete(project["id"])

    async def test_delete_project_as_worker_forbidden(self, client, test_worker, test_project, test_worker_email, test_worker_password):
        """Test worker cannot delete project (403)."""
        # Login as worker
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_worker_email,
            "password": test_worker_password
        })
        token = login_response.json()["access_token"]

        # Try to delete
        response = await client.delete(
            f"/api/v1/projects/{test_project['id']}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403

    async def test_delete_project_not_found(self, client, test_boss):
        """Test 404 when deleting non-existent project."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "boss@example.com",
            "password": "BossPass123!"
        })
        token = login_response.json()["access_token"]

        # Delete non-existent project
        response = await client.delete(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
