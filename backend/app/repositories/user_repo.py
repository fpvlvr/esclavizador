"""
User repository for data access.

Returns UserData TypedDicts for ORM independence.
"""

from typing import Optional
from datetime import date
from tortoise.queryset import Q
from tortoise.functions import Sum

from app.models.user import User
from app.domain.constants import UserRole
from app.models.organization import Organization
from app.models.time_entry import TimeEntry
from app.models.project import Project
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
        """Generic update - accepts any dict of User model fields."""
        user = await User.filter(id=user_id).first()

        if not user:
            return None

        for key, value in data.items():
            setattr(user, key, value)

        await user.save()
        return self._to_dict(user)

    async def list(
        self,
        org_id: str,
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """Multi-tenant list - auto-filtered by org_id."""
        query = self.model.filter(organization_id=org_id)

        if 'is_active' in filters and filters['is_active'] is not None:
            query = query.filter(is_active=filters['is_active'])

        if 'role' in filters and filters['role'] is not None:
            query = query.filter(role=filters['role'])

        total = await query.count()
        users = await query.offset(offset).limit(limit).order_by('-created_at').all()

        return {
            "items": [self._to_dict(user) for user in users],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    async def list_stats(
        self,
        org_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        filters: dict,
        limit: int,
        offset: int
    ) -> dict:
        """
        List users with aggregated stats (projects + time).

        For each user, calculates:
        - total_time_seconds: Sum of completed time entries in date range
        - projects: Unique projects worked on in date range
        """
        # Base query - users in org
        query = self.model.filter(organization_id=org_id)

        if 'is_active' in filters and filters['is_active'] is not None:
            query = query.filter(is_active=filters['is_active'])

        if 'role' in filters and filters['role'] is not None:
            query = query.filter(role=filters['role'])

        total = await query.count()
        users = await query.offset(offset).limit(limit).order_by('-created_at').all()

        # For each user, fetch stats
        items = []
        for user in users:
            # Build time entry filter for date range
            time_entry_filter = Q(user_id=user.id)

            if start_date:
                time_entry_filter &= Q(start_time__gte=start_date)

            if end_date:
                # Include entries that started before end of day
                time_entry_filter &= Q(start_time__lt=end_date)

            # Calculate total time (only completed entries have duration)
            time_entries = await TimeEntry.filter(time_entry_filter, is_running=False).all()

            total_seconds = 0
            for entry in time_entries:
                if entry.end_time and entry.start_time:
                    duration = (entry.end_time - entry.start_time).total_seconds()
                    total_seconds += int(duration)

            # Get unique projects (with prefetch for efficiency)
            project_ids = set()
            for entry in time_entries:
                project_ids.add(entry.project_id)

            # Fetch project details
            projects = []
            if project_ids:
                project_objs = await Project.filter(id__in=list(project_ids)).all()
                projects = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "color": p.color
                    }
                    for p in project_objs
                ]

            # Build user stats dict
            user_stats = {
                **self._to_dict(user),
                "total_time_seconds": total_seconds,
                "projects": projects
            }
            items.append(user_stats)

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }


# Singleton instance
user_repo = UserRepository()
