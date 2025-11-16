"""
Refresh token repository for data access.

Returns RefreshTokenData TypedDicts for ORM independence.
"""

from typing import Optional
from datetime import datetime, timezone

from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.base import BaseRepository
from app.domain.entities import RefreshTokenData


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenData]):
    """Repository for refresh token data access."""

    model = RefreshToken

    def _to_dict(self, token: RefreshToken) -> RefreshTokenData:
        """Convert RefreshToken ORM instance to RefreshTokenData dict."""
        return {
            "id": token.id,
            "user_id": token.user_id,
            "token_hash": token.token_hash,
            "expires_at": token.expires_at,
            "revoked_at": token.revoked_at,
            "created_at": token.created_at,
        }

    async def create_token(
        self,
        user_id: str,  # ID, not ORM object!
        token_hash: str,
        expires_at: datetime
    ) -> RefreshTokenData:
        """
        Store refresh token in database.

        Args:
            user_id: User UUID
            token_hash: SHA-256 hash of refresh token
            expires_at: Expiration timestamp

        Returns:
            Created refresh token as RefreshTokenData dict
        """
        # Repository handles ORM internally
        user = await User.get(id=user_id)

        token = await self.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at
        )

        # Convert ORM → RefreshTokenData dict using _to_dict
        return self._to_dict(token)

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshTokenData]:
        """
        Get refresh token by hash.

        Only returns tokens that are:
        - Not revoked (revoked_at is NULL)
        - Not expired (expires_at > now)

        Args:
            token_hash: SHA-256 hash of refresh token

        Returns:
            RefreshTokenData dict if found and valid, None otherwise
        """
        token = await RefreshToken.filter(
            token_hash=token_hash,
            revoked_at__isnull=True,  # Not revoked
            expires_at__gt=datetime.now(timezone.utc)  # Not expired
        ).first()

        if not token:
            return None

        # Convert ORM → RefreshTokenData dict using _to_dict
        return self._to_dict(token)

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
