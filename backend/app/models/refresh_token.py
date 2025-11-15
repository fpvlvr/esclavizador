"""
Refresh token model for JWT token revocation capability.

Security: Stores SHA-256 hash of refresh token, not plaintext.
"""

from tortoise import fields
from tortoise.models import Model


class RefreshToken(Model):
    """
    Refresh token storage for revocation capability.

    Refresh tokens are long-lived (7 days) and need to be revocable
    for security (logout, suspicious activity, etc.).

    We store SHA-256 hash instead of plaintext to prevent token leakage
    if the database is compromised.
    """

    id = fields.UUIDField(primary_key=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User",
        related_name="refresh_tokens",
        null=False,
        on_delete=fields.CASCADE,
        description="User who owns this refresh token"
    )
    token_hash = fields.CharField(
        max_length=64,  # SHA-256 produces 64 hex characters
        null=False,
        db_index=True,  # For fast lookup during refresh
        description="SHA-256 hash of the refresh token"
    )
    expires_at = fields.DatetimeField(
        null=False,
        description="When this refresh token expires"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    revoked_at = fields.DatetimeField(
        null=True,
        description="Timestamp when token was revoked (logout/security event)"
    )

    class Meta:
        table = "refresh_tokens"
        indexes = ["user_id", "token_hash"]

    def __str__(self) -> str:
        status = "revoked" if self.revoked_at else "active"
        return f"RefreshToken(user_id={self.user_id}, status={status})"
