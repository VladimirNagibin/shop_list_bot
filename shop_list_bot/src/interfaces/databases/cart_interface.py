"""Async cart repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from schemas.models import CartCreate, CartInDB, CartUpdate

from .base import IRepository


class ICartRepository(IRepository[CartInDB, CartCreate, CartUpdate], ABC):
    """Async cart repository interface with user management methods."""

    @abstractmethod
    async def get_carts_by_user(self, user_id: UUID) -> list[tuple[CartInDB, str]]:
        """Get all carts for a user with their roles asynchronously."""

    @abstractmethod
    async def add_user_to_cart(
        self, user_id: UUID, cart_id: UUID, role: str = "viewer"
    ) -> bool:
        """Add user to cart with specified role asynchronously."""

    @abstractmethod
    async def remove_user_from_cart(self, user_id: UUID, cart_id: UUID) -> bool:
        """Remove user from cart asynchronously."""

    @abstractmethod
    async def update_user_role(self, user_id: UUID, cart_id: UUID, role: str) -> bool:
        """Update user's role in cart asynchronously."""

    @abstractmethod
    async def get_cart_users(self, cart_id: UUID) -> list[tuple[UUID, str]]:
        """Get all users in a cart with their roles asynchronously."""

    @abstractmethod
    async def get_cart_owner(self, cart_id: UUID) -> UUID | None:
        """Get the owner of a cart asynchronously."""

    @abstractmethod
    async def create_cart_with_owner(
        self, data: CartCreate, owner_id: UUID
    ) -> CartInDB | None:
        """Create a cart and assign an owner asynchronously."""

    @abstractmethod
    async def get_with_products(self, cart_id: UUID) -> CartInDB | None:
        """Get cart with all products (eager loading) asynchronously."""

    @abstractmethod
    async def get_with_users_and_products(self, cart_id: UUID) -> CartInDB | None:
        """Get cart with users and products (full eager loading) asynchronously."""

    # @abstractmethod
    # async def add_users_to_cart(
    #    self, cart_id: UUID, user_roles: list[tuple[UUID, str]]
    # ) -> int:
    #    """Add multiple users to cart asynchronously."""
