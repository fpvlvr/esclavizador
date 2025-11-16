"""
User repository for data access.

Returns UserData TypedDicts for ORM independence.
"""

from typing import Optional

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.repositories.base import BaseRepository
from app.domain.entities import UserData


class UserRepository(BaseRepository[User, UserData]):
    """Repository for user data access."""

    model = User

    def _to_dict(self, user: User) -> UserData:
        """Convert User ORM instance to UserData dict."""
        return {
            "id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
            "role": user.role.value,
            "organization_id": user.organization_id,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }

    async def get_by_email(self, email: str) -> Optional[UserData]:
        """
        Get user by email address.

        Args:
            email: User email (case-sensitive)

        Returns:
            UserData dict if found, None otherwise
        """
        user = await User.filter(email=email).first()

        if not user:
            return None

        # Convert ORM → UserData dict using _to_dict
        return self._to_dict(user)

    async def create_user(
        self,
        email: str,
        password_hash: str,
        role: UserRole,
        organization_id: str  # ID, not ORM object!
    ) -> UserData:
        """
        Create new user.

        Args:
            email: User email
            password_hash: Hashed password (Argon2id)
            role: User role (BOSS or WORKER)
            organization_id: Organization UUID

        Returns:
            Created user as UserData dict
        """
        # Repository handles ORM internally
        org = await Organization.get(id=organization_id)

        user = await self.create(
            email=email,
            password_hash=password_hash,
            role=role,
            organization=org
        )

        # Convert ORM → UserData dict using _to_dict
        return self._to_dict(user)

    async def get_by_id(self, user_id: str) -> Optional[UserData]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            UserData dict if found, None otherwise
        """
        user = await User.filter(id=user_id).first()

        if not user:
            return None

        # Convert ORM → UserData dict using _to_dict
        return self._to_dict(user)

    async def update(self, user_id: str, data: dict) -> Optional[UserData]:
        """
        Update user fields.

        Args:
            user_id: User UUID
            data: Dict of fields to update (e.g., {"is_active": False})

        Returns:
            Updated user data dict, or None if not found
        """
        user = await User.filter(id=user_id).first()

        if not user:
            return None

        # Update fields
        for key, value in data.items():
            setattr(user, key, value)

        await user.save()

        # Convert ORM → UserData dict using _to_dict
        return self._to_dict(user)


# Singleton instance
user_repo = UserRepository()
