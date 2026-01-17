"""Async user repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from schemas.models import UserCreate, UserInDB, UserUpdate

from .base import IRepository


class IUserRepository(IRepository[UserInDB, UserCreate, UserUpdate], ABC):
    """Async user repository interface with Telegram-specific methods."""

    @abstractmethod
    async def get_by_tg_id(self, tg_id: int) -> UserInDB | None:
        """Get user by Telegram ID asynchronously."""

    @abstractmethod
    async def get_by_username(self, username: str) -> UserInDB | None:
        """Get user by username asynchronously."""

    @abstractmethod
    async def search_by_name(self, name_query: str) -> list[UserInDB]:
        """Search users by first name asynchronously."""

    @abstractmethod
    async def get_users_in_cart(self, cart_id: UUID) -> list[UserInDB]:
        """Get all users in a specific cart asynchronously."""

    @abstractmethod
    async def create_or_update_by_tg_id(self, tg_id: int, data: UserCreate) -> UserInDB:
        """Create or update user by Telegram ID asynchronously."""

    @abstractmethod
    async def get_with_carts(self, user_id: UUID) -> UserInDB | None:
        """Get user with their carts (eager loading) asynchronously."""

    @abstractmethod
    async def bulk_create(self, users_data: list[UserCreate]) -> list[UserInDB]:
        """Create multiple users asynchronously."""
