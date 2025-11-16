"""
Base repository with common CRUD operations.

ORM-independent base repository that returns TypedDict entities.
Subclasses must implement _to_dict() for entity conversion.
"""

from typing import TypeVar, Generic, Type, Optional, Dict, Any
from abc import ABC, abstractmethod
from uuid import UUID
from tortoise.models import Model


ModelType = TypeVar("ModelType", bound=Model)
EntityType = TypeVar("EntityType", bound=Dict[str, Any])


class BaseRepository(Generic[ModelType, EntityType], ABC):
    """
    Abstract base repository with common CRUD operations.

    Returns TypedDict entities instead of ORM objects for ORM independence.
    Subclasses must implement _to_dict() to convert ORM → TypedDict.

    Usage:
        class UserRepository(BaseRepository[User, UserData]):
            model = User

            def _to_dict(self, user: User) -> UserData:
                return {
                    "id": user.id,
                    "email": user.email,
                    # ... other fields
                }
    """

    model: Type[ModelType]

    @abstractmethod
    def _to_dict(self, instance: ModelType) -> EntityType:
        """
        Convert ORM instance to TypedDict entity.

        Must be implemented by subclass to define entity structure.

        Args:
            instance: ORM model instance

        Returns:
            TypedDict entity
        """
        pass

    async def get_by_id(self, id: UUID | str) -> Optional[EntityType]:
        """
        Get entity by ID.

        Args:
            id: UUID or UUID string

        Returns:
            TypedDict entity if found, None otherwise
        """
        instance = await self.model.get_or_none(id=id)
        return self._to_dict(instance) if instance else None

    async def create(self, **kwargs) -> ModelType:
        """
        Create new model instance (returns ORM for internal use).

        Args:
            **kwargs: Model field values

        Returns:
            Created ORM model instance (for internal conversion)
        """
        return await self.model.create(**kwargs)

    async def delete(self, id: UUID | str) -> bool:
        """
        Delete entity by ID.

        Args:
            id: UUID or UUID string

        Returns:
            True if deleted, False if not found
        """
        instance = await self.model.get_or_none(id=id)
        if instance:
            await instance.delete()
            return True
        return False
