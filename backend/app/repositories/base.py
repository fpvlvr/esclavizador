"""
Base repository with common CRUD operations.

Uses generic typing to provide type-safe repository pattern.
"""

from typing import TypeVar, Generic, Type, Optional
from tortoise.models import Model


ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository(Generic[ModelType]):
    """
    Abstract base repository with common CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            model = User

            # Add model-specific methods here
    """

    model: Type[ModelType]

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """
        Get model instance by ID.

        Args:
            id: UUID string

        Returns:
            Model instance if found, None otherwise
        """
        return await self.model.get_or_none(id=id)

    async def create(self, **kwargs) -> ModelType:
        """
        Create new model instance.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        return await self.model.create(**kwargs)

    async def delete(self, id: str) -> bool:
        """
        Delete model instance by ID.

        Args:
            id: UUID string

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id)
        if instance:
            await instance.delete()
            return True
        return False
