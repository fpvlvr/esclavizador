"""
User repository for data access.
"""

from typing import Optional

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user data access."""

    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email (case-sensitive)

        Returns:
            User if found, None otherwise
        """
        return await User.filter(email=email).first()

    async def create_user(
        self,
        email: str,
        password_hash: str,
        role: UserRole,
        organization: Organization
    ) -> User:
        """
        Create new user.

        Args:
            email: User email
            password_hash: Hashed password (Argon2id)
            role: User role (MASTER or SLAVE)
            organization: Organization instance

        Returns:
            Created user
        """
        return await self.create(
            email=email,
            password_hash=password_hash,
            role=role,
            organization=organization
        )

    async def get_by_id_with_org(self, user_id: str) -> Optional[User]:
        """
        Get user by ID with organization prefetched.

        Args:
            user_id: User UUID

        Returns:
            User with organization, or None
        """
        return await User.filter(id=user_id).prefetch_related("organization").first()


# Singleton instance
user_repo = UserRepository()
