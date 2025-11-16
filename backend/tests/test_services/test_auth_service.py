"""
Tests for AuthService and security functions.

Tests:
- Security functions (password hashing, validation, JWT tokens)
- Auth service business logic (register, authenticate, refresh, logout)
"""

import pytest
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException

from app.services.auth_service import auth_service
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.core.config import settings
from app.models.user import UserRole
from app.repositories.organization_repo import organization_repo
from app.repositories.user_repo import user_repo
from app.repositories.refresh_token_repo import refresh_token_repo


class TestSecurityFunctions:
    """Test password hashing and validation functions."""

    def test_hash_password(self):
        """Test password hashing creates different hashes for same password."""
        password = "TestPassword123!"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (Argon2id uses random salt)
        assert hash1 != hash2
        # Both should be Argon2id format
        assert hash1.startswith("$argon2id$")
        assert hash2.startswith("$argon2id$")

    def test_verify_password_correct(self):
        """Test correct password verifies successfully."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_wrong(self):
        """Test wrong password fails verification."""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)
        assert result is False

    def test_validate_password_strength_valid(self):
        """Test strong password passes validation."""
        password = "StrongPass123!"

        is_valid, error = validate_password_strength(password)

        assert is_valid is True
        assert error == ""

    def test_validate_password_strength_too_short(self):
        """Test short password fails validation."""
        password = "Short1!"

        is_valid, error = validate_password_strength(password)

        assert is_valid is False
        assert "at least 8 characters" in error

    def test_validate_password_strength_no_uppercase(self):
        """Test password without uppercase fails."""
        password = "lowercase123!"

        is_valid, error = validate_password_strength(password)

        assert is_valid is False
        assert "uppercase" in error

    def test_validate_password_strength_no_lowercase(self):
        """Test password without lowercase fails."""
        password = "UPPERCASE123!"

        is_valid, error = validate_password_strength(password)

        assert is_valid is False
        assert "lowercase" in error

    def test_validate_password_strength_no_digit(self):
        """Test password without digit fails."""
        password = "NoDigitsHere!"

        is_valid, error = validate_password_strength(password)

        assert is_valid is False
        assert "digit" in error

    def test_validate_password_strength_no_special(self):
        """Test password without special character fails."""
        password = "NoSpecial123"

        is_valid, error = validate_password_strength(password)

        assert is_valid is False
        assert "special character" in error


class TestJWTTokenFunctions:
    """Test JWT token creation and decoding."""

    def test_create_access_token(self):
        """Test access token generation with correct claims."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        email = "test@example.com"
        role = "master"
        org_id = "660e8400-e29b-41d4-a716-446655440000"

        token = create_access_token(user_id, email, role, org_id)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify claims
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
        assert payload["org_id"] == org_id
        assert payload["type"] == "access"

    def test_decode_access_token(self):
        """Test decoding valid access token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id, "test@example.com", "slave", "org-id")

        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["email"] == "test@example.com"
        assert payload["role"] == "slave"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token(self):
        """Test expired token raises exception."""
        # Create token that expired 1 hour ago
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now(timezone.utc)
        expire = now - timedelta(hours=1)  # Expired

        payload = {
            "sub": user_id,
            "email": "test@example.com",
            "role": "master",
            "org_id": "org-id",
            "exp": expire,
            "iat": now - timedelta(hours=2),
            "type": "access"
        }

        expired_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

        # Should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired_token)

    def test_create_refresh_token(self):
        """Test refresh token generation with JTI."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        token, jti = create_refresh_token(user_id)

        assert token is not None
        assert jti is not None
        assert isinstance(token, str)
        assert isinstance(jti, str)

        # Decode and verify claims
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_hash_token(self):
        """Test token hashing is consistent."""
        token = "sample_refresh_token_12345"

        hash1 = hash_token(token)
        hash2 = hash_token(token)

        # Same input should produce same hash (SHA-256 is deterministic)
        assert hash1 == hash2
        # Should be 64 hex characters (SHA-256)
        assert len(hash1) == 64


class TestAuthService:
    """Test AuthService business logic."""

    async def test_register_new_user_new_org(self):
        """Test registering new user creates user and organization."""
        user = await auth_service.register(
            email="newuser@example.com",
            password="NewPass123!",
            role=UserRole.MASTER,
            organization_name="New Test Org"
        )

        assert user is not None
        assert user["email"] == "newuser@example.com"
        assert user["role"] == "master"
        assert user["is_active"] is True

        # Verify organization was created
        org = await organization_repo.get_by_id(str(user["organization_id"]))
        assert org is not None
        assert org["name"] == "New Test Org"

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_register_org_name_exists(self):
        """Test registration raises 409 when org name already exists."""
        # Create existing organization
        existing_org = await organization_repo.create_organization(name="Existing Org")

        # Try to register with same org name
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(
                email="newuser@example.com",
                password="NewPass123!",
                role=UserRole.MASTER,
                organization_name="Existing Org"  # Already exists
            )

        assert exc_info.value.status_code == 409
        assert "Organization name already exists" in exc_info.value.detail

        # Cleanup
        await organization_repo.delete(existing_org["id"])

    async def test_register_duplicate_email(self):
        """Test registration raises 409 for duplicate email."""
        # Create existing user
        org = await organization_repo.create_organization(name="Email Test Org")
        existing_user = await user_repo.create_user(
            email="existing@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=str(org["id"])
        )

        # Try to register with same email
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(
                email="existing@example.com",  # Already exists
                password="NewPass123!",
                role=UserRole.MASTER,
                organization_name="Another Org"
            )

        assert exc_info.value.status_code == 409
        assert "Email already registered" in exc_info.value.detail

        # Cleanup
        await user_repo.delete(existing_user["id"])
        await organization_repo.delete(org["id"])

    async def test_authenticate_success(self):
        """Test successful authentication returns user and tokens."""
        # Create test user
        org = await organization_repo.create_organization(name="Auth Test Org")
        password = "AuthPass123!"
        user = await user_repo.create_user(
            email="authuser@example.com",
            password_hash=hash_password(password),
            role=UserRole.MASTER,
            organization_id=str(org["id"])
        )

        # Authenticate
        returned_user, access_token, refresh_token = await auth_service.authenticate(
            email="authuser@example.com",
            password=password
        )

        assert returned_user["id"] == user["id"]
        assert returned_user["email"] == "authuser@example.com"
        assert access_token is not None
        assert refresh_token is not None

        # Verify access token claims
        payload = decode_token(access_token)
        assert payload["sub"] == str(user["id"])
        assert payload["email"] == "authuser@example.com"
        assert payload["role"] == "master"

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_authenticate_wrong_password(self):
        """Test authentication with wrong password raises 401."""
        org = await organization_repo.create_organization(name="Wrong Pass Org")
        user = await user_repo.create_user(
            email="wrongpass@example.com",
            password_hash=hash_password("CorrectPass123!"),
            role=UserRole.SLAVE,
            organization_id=str(org["id"])
        )

        # Try to authenticate with wrong password
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate(
                email="wrongpass@example.com",
                password="WrongPass123!"
            )

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_authenticate_inactive_user(self):
        """Test authentication with inactive user raises 403."""
        org = await organization_repo.create_organization(name="Inactive User Org")
        user = await user_repo.create_user(
            email="inactive@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=str(org["id"])
        )
        # Mark user as inactive
        await user_repo.update(user["id"], {"is_active": False})

        # Try to authenticate
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate(
                email="inactive@example.com",
                password="Password123!"
            )

        assert exc_info.value.status_code == 403
        assert "Inactive account" in exc_info.value.detail

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_refresh_token_success(self):
        """Test refreshing access token returns new token."""
        # Create user and authenticate to get refresh token
        org = await organization_repo.create_organization(name="Refresh Test Org")
        user = await user_repo.create_user(
            email="refresh@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.MASTER,
            organization_id=str(org["id"])
        )

        _, _, refresh_token = await auth_service.authenticate(
            email="refresh@example.com",
            password="Password123!"
        )

        # Refresh access token
        new_access_token = await auth_service.refresh_access_token(refresh_token)

        assert new_access_token is not None
        assert isinstance(new_access_token, str)

        # Verify new token is valid
        payload = decode_token(new_access_token)
        assert payload["sub"] == str(user["id"])
        assert payload["type"] == "access"

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_refresh_token_revoked(self):
        """Test refreshing revoked token raises 401."""
        # Create user and authenticate
        org = await organization_repo.create_organization(name="Revoked Token Org")
        user = await user_repo.create_user(
            email="revoked@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.SLAVE,
            organization_id=str(org["id"])
        )

        _, _, refresh_token = await auth_service.authenticate(
            email="revoked@example.com",
            password="Password123!"
        )

        # Revoke the token
        token_hash = hash_token(refresh_token)
        await refresh_token_repo.revoke_token(token_hash)

        # Try to refresh with revoked token
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(refresh_token)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired refresh token" in exc_info.value.detail

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])

    async def test_logout_success(self):
        """Test logout revokes refresh token."""
        # Create user and authenticate
        org = await organization_repo.create_organization(name="Logout Test Org")
        user = await user_repo.create_user(
            email="logout@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.MASTER,
            organization_id=str(org["id"])
        )

        _, _, refresh_token = await auth_service.authenticate(
            email="logout@example.com",
            password="Password123!"
        )

        # Logout
        await auth_service.logout(refresh_token)

        # Verify token is revoked (cannot refresh)
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(refresh_token)

        assert exc_info.value.status_code == 401

        # Cleanup
        await user_repo.delete(user["id"])
        await organization_repo.delete(org["id"])
