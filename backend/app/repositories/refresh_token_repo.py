"""
Refresh token repository for data access.
"""

from typing import Optional
from datetime import datetime, timezone

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token data access."""

    model = RefreshToken

    async def create_token(
        self,
        user: User,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """
        Store refresh token in database.

        Args:
            user: User instance
            token_hash: SHA-256 hash of refresh token
            expires_at: Expiration timestamp

        Returns:
            Created RefreshToken instance
        """
        return await self.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at
        )

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """
        Get refresh token by hash.

        Only returns tokens that are:
        - Not revoked (revoked_at is NULL)
        - Not expired (expires_at > now)

        Args:
            token_hash: SHA-256 hash of refresh token

        Returns:
            RefreshToken if found and valid, None otherwise
        """
        return await RefreshToken.filter(
            token_hash=token_hash,
            revoked_at__isnull=True,  # Not revoked
            expires_at__gt=datetime.now(timezone.utc)  # Not expired
        ).first()

    async def revoke_token(self, token_hash: str) -> bool:
        """
        Revoke refresh token (logout).

        Args:
            token_hash: SHA-256 hash of refresh token

        Returns:
            True if token was revoked, False if not found
        """
        token = await RefreshToken.filter(token_hash=token_hash).first()
        if token:
            token.revoked_at = datetime.now(timezone.utc)
            await token.save()
            return True
        return False

    async def cleanup_expired(self) -> int:
        """
        Delete expired refresh tokens (cleanup job for future).

        Returns:
            Number of tokens deleted
        """
        result = await RefreshToken.filter(
            expires_at__lt=datetime.now(timezone.utc)
        ).delete()
        return result


# Singleton instance
refresh_token_repo = RefreshTokenRepository()
