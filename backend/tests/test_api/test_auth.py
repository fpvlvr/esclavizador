"""
API integration tests for authentication endpoints.

Tests all auth endpoints:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

Tests cover success scenarios, validation errors, and business logic errors.
"""

from datetime import datetime, timedelta, timezone
import jwt

from app.core.security import create_access_token, create_refresh_token, hash_token
from app.core.config import settings
from app.repositories.organization_repo import organization_repo
from app.repositories.user_repo import user_repo
from app.repositories.refresh_token_repo import refresh_token_repo


class TestRegisterEndpoint:
    """Test POST /api/v1/auth/register endpoint."""

    async def test_register_success_new_org(self, client):
        """Test successful registration creates user and organization."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "role": "master",
            "organization_name": "Brand New Org"
        })

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == "newuser@example.com"
        assert data["role"] == "master"
        assert data["is_active"] is True
        assert "id" in data
        assert "organization_id" in data
        assert "created_at" in data

        # Cleanup
        user = await user_repo.get_by_email("newuser@example.com")
        org = await organization_repo.get_by_id(user["organization_id"])
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_register_org_already_exists(self, client, test_org):
        """Test registration with existing org name returns 409."""
        # test_org already exists with name "Test Org"
        response = await client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "role": "slave",
            "organization_name": "Test Org"  # Already exists
        })

        assert response.status_code == 409
        assert "Organization name already exists" in response.json()["detail"]

    async def test_register_duplicate_email(self, client, test_slave, test_slave_email):
        """Test registration with existing email returns 409."""
        # test_slave already exists with email from test_slave_email fixture
        response = await client.post("/api/v1/auth/register", json={
            "email": test_slave_email,  # Already exists
            "password": "SecurePass123!",
            "role": "master",
            "organization_name": "Another Org"
        })

        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    async def test_register_weak_password_short(self, client):
        """Test registration with short password returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "Short1!",  # Only 7 characters
            "role": "slave",
            "organization_name": "Test Org"
        })

        assert response.status_code == 422
        assert "detail" in response.json()

    async def test_register_weak_password_no_uppercase(self, client):
        """Test registration without uppercase letter returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "lower@example.com",
            "password": "lowercase123!",  # No uppercase
            "role": "slave",
            "organization_name": "Test Org"
        })

        assert response.status_code == 422
        data = response.json()
        assert "uppercase" in str(data).lower()

    async def test_register_weak_password_no_digit(self, client):
        """Test registration without digit returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "nodigit@example.com",
            "password": "NoDigitsHere!",  # No digit
            "role": "slave",
            "organization_name": "Test Org"
        })

        assert response.status_code == 422
        data = response.json()
        assert "digit" in str(data).lower()

    async def test_register_weak_password_no_special(self, client):
        """Test registration without special character returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "nospecial@example.com",
            "password": "NoSpecial123",  # No special character
            "role": "slave",
            "organization_name": "Test Org"
        })

        assert response.status_code == 422
        data = response.json()
        assert "special" in str(data).lower()

    async def test_register_invalid_email(self, client):
        """Test registration with invalid email format returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",  # Invalid format
            "password": "SecurePass123!",
            "role": "slave",
            "organization_name": "Test Org"
        })

        assert response.status_code == 422

    async def test_register_invalid_role(self, client):
        """Test registration with invalid role returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "role@example.com",
            "password": "SecurePass123!",
            "role": "admin",  # Invalid role (should be master/slave)
            "organization_name": "Test Org"
        })

        assert response.status_code == 422

    async def test_register_empty_org_name(self, client):
        """Test registration with empty org name returns 422."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "org@example.com",
            "password": "SecurePass123!",
            "role": "master",
            "organization_name": ""  # Empty
        })

        assert response.status_code == 422


class TestLoginEndpoint:
    """Test POST /api/v1/auth/login endpoint."""

    async def test_login_success(self, client, test_slave, test_slave_email, test_slave_password):
        """Test successful login returns tokens."""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client, test_slave, test_slave_email, test_slave_password):
        """Test login with wrong password returns 401."""
        response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_wrong_email(self, client):
        """Test login with non-existent email returns 401."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        })

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    async def test_login_inactive_account(self, client, test_slave, test_slave_email, test_slave_password):
        """Test login with inactive account returns 403."""
        # Make user inactive via repository
        await user_repo.update(test_slave["id"], {"is_active": False})

        response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })

        assert response.status_code == 403
        assert "Inactive account" in response.json()["detail"]

        # Restore active status for cleanup
        await user_repo.update(test_slave["id"], {"is_active": True})

    async def test_login_invalid_email_format(self, client):
        """Test login with invalid email format returns 422."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "not-valid-email",
            "password": "Password123!"
        })

        assert response.status_code == 422


class TestRefreshEndpoint:
    """Test POST /api/v1/auth/refresh endpoint."""

    async def test_refresh_token_success(self, client, test_slave, test_slave_email, test_slave_password):
        """Test refreshing token returns new access token."""
        # Login to get refresh token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Should NOT return new refresh token (reuse existing)
        assert "refresh_token" not in data

    async def test_refresh_token_expired(self, client, test_slave, test_slave_email, test_slave_password):
        """Test refreshing expired token returns 401."""
        # Create expired refresh token
        now = datetime.now(timezone.utc)
        expire = now - timedelta(days=1)  # Expired

        payload = {
            "sub": str(test_slave["id"]),
            "type": "refresh",
            "exp": expire,
            "iat": now - timedelta(days=2),
            "jti": "expired-jti"
        }

        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": expired_token
        })

        assert response.status_code == 401

    async def test_refresh_token_invalid(self, client):
        """Test refreshing with invalid token returns 401."""
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "completely_invalid_token"
        })

        assert response.status_code == 401

    async def test_refresh_token_revoked(self, client, test_slave, test_slave_email, test_slave_password):
        """Test refreshing revoked token returns 401."""
        # Login to get refresh token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        refresh_token = login_response.json()["refresh_token"]

        # Revoke the token
        token_hash = hash_token(refresh_token)
        await refresh_token_repo.revoke_token(token_hash)

        # Try to refresh
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]


class TestLogoutEndpoint:
    """Test POST /api/v1/auth/logout endpoint."""

    async def test_logout_success(self, client, test_slave, test_slave_email, test_slave_password):
        """Test logout revokes refresh token."""
        # Login to get refresh token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = await client.post("/api/v1/auth/logout", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 204

    async def test_logout_invalid_token(self, client):
        """Test logout with invalid token returns 401."""
        response = await client.post("/api/v1/auth/logout", json={
            "refresh_token": "invalid_token"
        })

        assert response.status_code == 401

    async def test_logout_then_refresh_fails(self, client, test_slave, test_slave_email, test_slave_password):
        """Test that refreshing after logout returns 401."""
        # Login
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        await client.post("/api/v1/auth/logout", json={
            "refresh_token": refresh_token
        })

        # Try to refresh (should fail)
        response = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 401


class TestGetMeEndpoint:
    """Test GET /api/v1/auth/me endpoint."""

    async def test_get_me_success(self, client, test_slave, test_slave_email, test_slave_password):
        """Test getting current user with valid token."""
        # Login to get access token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        access_token = login_response.json()["access_token"]

        # Get me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == test_slave_email
        assert data["role"] == "slave"
        assert data["is_active"] is True
        assert "id" in data
        assert "organization_id" in data

    async def test_get_me_no_token(self, client):
        """Test /me without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    async def test_get_me_expired_token(self, client, test_slave, test_slave_email, test_slave_password):
        """Test /me with expired token returns 401."""
        # Create expired access token
        now = datetime.now(timezone.utc)
        expire = now - timedelta(hours=1)  # Expired

        payload = {
            "sub": str(test_slave["id"]),
            "email": test_slave["email"],
            "role": test_slave["role"],
            "org_id": str(test_slave["organization_id"]),
            "exp": expire,
            "iat": now - timedelta(hours=2),
            "type": "access"
        }

        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client):
        """Test /me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    async def test_get_me_inactive_account(self, client, test_slave, test_slave_email, test_slave_password):
        """Test /me with inactive account returns 403."""
        # Login first (while active)
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        access_token = login_response.json()["access_token"]

        # Make user inactive via repository
        await user_repo.update(test_slave["id"], {"is_active": False})

        # Try to access /me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 403

        # Restore active status for cleanup
        await user_repo.update(test_slave["id"], {"is_active": True})


class TestRoleBasedAccess:
    """Test role-based access control."""

    async def test_protected_route_master_access(self, client, test_master):
        """Test master user can access master-only routes."""
        # Login as master
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "master@example.com",
            "password": "MasterPass123!"
        })
        access_token = login_response.json()["access_token"]

        # Access /me (works for all roles)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["role"] == "master"

    async def test_protected_route_slave_access(self, client, test_slave, test_slave_email, test_slave_password):
        """Test slave user can access regular protected routes."""
        # Login as slave
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_slave_email,
            "password": test_slave_password
        })
        access_token = login_response.json()["access_token"]

        # Access /me (works for all roles)
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["role"] == "slave"
