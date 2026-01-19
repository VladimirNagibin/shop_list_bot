"""Async product repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from schemas.models import ProductCreate, ProductInDB, ProductUpdate

from .base import IRepository


class IProductRepository(IRepository[ProductInDB, ProductCreate, ProductUpdate], ABC):
    """Async product repository interface with cart management methods."""

    @abstractmethod
    async def search_by_name(
        self, name_query: str, limit: int = 20
    ) -> list[ProductInDB]:
        """Search products by name asynchronously."""

    @abstractmethod
    async def add_product_to_cart(self, product_id: UUID, cart_id: UUID) -> bool:
        """Add product to cart asynchronously."""

    @abstractmethod
    async def remove_product_from_cart(self, product_id: UUID, cart_id: UUID) -> bool:
        """Remove product from cart asynchronously."""

    @abstractmethod
    async def get_products_in_cart(self, cart_id: UUID) -> list[ProductInDB]:
        """Get all products in a cart asynchronously."""

    @abstractmethod
    async def get_carts_with_product(self, product_id: UUID) -> list[UUID]:
        """Get all carts containing a specific product asynchronously."""

    @abstractmethod
    async def batch_add_to_cart(self, product_ids: list[UUID], cart_id: UUID) -> int:
        """Add multiple products to cart at once asynchronously."""

    # @abstractmethod
    # async def get_popular_products(self, limit: int = 10) -> list[ProductInDB]:
    #     """Get most frequently added products asynchronously."""

    # @abstractmethod
    # async def get_products_with_filters(
    #     self, filters: dict[str, Any], skip: int = 0, limit: int = 50
    # ) -> list[ProductInDB]:
    #     """Get products with complex filters asynchronously."""

    # @abstractmethod
    # async def bulk_create(
    #    self, products_data: list[ProductCreate]
    # ) -> list[ProductInDB]:
    #    """Create multiple products asynchronously."""
