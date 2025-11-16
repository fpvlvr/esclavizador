"""
Tests for RefreshTokenRepository.

Tests refresh token storage, retrieval, revocation, and cleanup.
"""

import pytest
from datetime import datetime, timedelta, timezone

from app.repositories.refresh_token_repo import refresh_token_repo
from app.core.security import hash_token


class TestRefreshTokenRepository:
    """Test refresh token repository data access."""

    async def test_create_token(self, test_worker):
        """Test creating a refresh token."""
        token_hash = hash_token("sample_refresh_token_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        assert refresh_token is not None
        assert refresh_token["id"] is not None
        assert refresh_token["user_id"] == test_worker["id"]
        assert refresh_token["token_hash"] == token_hash
        assert refresh_token["expires_at"] == expires_at
        assert refresh_token["revoked_at"] is None
        assert refresh_token["created_at"] is not None

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_get_by_hash_valid_token(self, test_worker):
        """Test getting valid (non-revoked, non-expired) token by hash."""
        token_hash = hash_token("valid_token_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Get by hash
        fetched_token = await refresh_token_repo.get_by_hash(token_hash)

        assert fetched_token is not None
        assert fetched_token["id"] == refresh_token["id"]
        assert fetched_token["token_hash"] == token_hash

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_get_by_hash_revoked_token(self, test_worker):
        """Test that revoked token is not returned."""
        token_hash = hash_token("revoked_token_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Revoke the token (using repository method, not ORM)
        await refresh_token_repo.revoke_token(token_hash)

        # Try to get by hash (should return None)
        fetched_token = await refresh_token_repo.get_by_hash(token_hash)

        assert fetched_token is None

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_get_by_hash_expired_token(self, test_worker):
        """Test that expired token is not returned."""
        token_hash = hash_token("expired_token_12345")
        # Set expiry to 1 second ago
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Try to get by hash (should return None because expired)
        fetched_token = await refresh_token_repo.get_by_hash(token_hash)

        assert fetched_token is None

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_get_by_hash_not_found(self):
        """Test getting non-existent token hash returns None."""
        result = await refresh_token_repo.get_by_hash("nonexistent_hash_12345")
        assert result is None

    async def test_revoke_token(self, test_worker):
        """Test revoking a refresh token."""
        token_hash = hash_token("to_revoke_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Revoke token
        revoked = await refresh_token_repo.revoke_token(token_hash)
        assert revoked is True

        # Verify get_by_hash returns None for revoked token
        fetched = await refresh_token_repo.get_by_hash(token_hash)
        assert fetched is None

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_revoke_nonexistent_token(self):
        """Test revoking non-existent token returns False."""
        revoked = await refresh_token_repo.revoke_token("nonexistent_hash")
        assert revoked is False

    async def test_cleanup_expired_tokens(self, test_worker):
        """Test cleanup of expired tokens."""
        # Create expired token
        expired_hash = hash_token("expired_cleanup_12345")
        expired_at = datetime.now(timezone.utc) - timedelta(days=1)
        expired_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=expired_hash,
            expires_at=expired_at
        )

        # Create valid token
        valid_hash = hash_token("valid_cleanup_12345")
        valid_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        valid_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=valid_hash,
            expires_at=valid_expires_at
        )

        # Run cleanup
        deleted_count = await refresh_token_repo.cleanup_expired()

        assert deleted_count >= 1  # At least our expired token

        # Verify expired token is deleted (use repository, not ORM)
        result = await refresh_token_repo.get_by_hash(expired_hash)
        assert result is None

        # Verify valid token still exists (use repository, not ORM)
        result = await refresh_token_repo.get_by_hash(valid_hash)
        assert result is not None

        # Cleanup
        await refresh_token_repo.delete(valid_token["id"])

    async def test_get_by_id(self, test_worker):
        """Test getting refresh token by ID."""
        token_hash = hash_token("id_lookup_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Get by ID (inherited from BaseRepository)
        fetched = await refresh_token_repo.get_by_id(str(refresh_token["id"]))

        assert fetched is not None
        assert fetched["id"] == refresh_token["id"]
        assert fetched["token_hash"] == token_hash

        # Cleanup
        await refresh_token_repo.delete(refresh_token["id"])

    async def test_delete_refresh_token(self, test_worker):
        """Test deleting refresh token by ID."""
        token_hash = hash_token("delete_token_12345")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        refresh_token = await refresh_token_repo.create_token(
            user_id=str(test_worker["id"]),
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Delete (using repository method, not ORM)
        deleted = await refresh_token_repo.delete(str(refresh_token["id"]))
        assert deleted is True

        # Verify deletion (using repository method, not ORM)
        result = await refresh_token_repo.get_by_id(str(refresh_token["id"]))
        assert result is None
