"""Product repository with CRUD operations."""

import sqlite3

from uuid import UUID

from core.logger import logger
from interfaces.databases.product_interface import IProductRepository
from schemas.models import ProductCreate, ProductInDB, ProductUpdate

from .base_sqlite import SQLiteBaseRepository


class SQLiteProductRepository(
    SQLiteBaseRepository[ProductInDB, ProductCreate, ProductUpdate],
    IProductRepository,
):
    """Async SQLite implementation of products table."""

    def __init__(self) -> None:
        super().__init__("products", ProductInDB)

    async def search_by_name(
        self, name_query: str, limit: int = 20
    ) -> list[ProductInDB]:
        """Search products by name."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT * FROM products
                WHERE name LIKE ?
                ORDER BY name
                LIMIT ?
            """,
                (f"%{name_query}%", limit),
            )

            rows = await cursor.fetchall()
            return [self._row_to_model(dict(row)) for row in rows]

    async def add_product_to_cart(self, product_id: UUID, cart_id: UUID) -> bool:
        """Add product to cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    """
                    INSERT OR IGNORE INTO product_cart (product_id, cart_id)
                    VALUES (?, ?)
                """,
                    (str(product_id), str(cart_id)),
                )
                logger.debug(f"Added product {product_id} to cart {cart_id}")
            except sqlite3.Error as e:
                logger.error(f"Error adding product to cart: {e}")
                return False
            else:
                return True

    async def remove_product_from_cart(self, product_id: UUID, cart_id: UUID) -> bool:
        """Remove product from cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                DELETE FROM product_cart
                WHERE product_id = ? AND cart_id = ?
            """,
                (str(product_id), str(cart_id)),
            )

            # TODO: Add product to achcive

            if cursor.rowcount > 0:
                logger.debug(f"Removed product {product_id} from cart {cart_id}")
                return True
            return False

    async def get_products_in_cart(self, cart_id: UUID) -> list[ProductInDB]:
        """Get all products in a cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT p.*
                FROM products p
                JOIN product_cart pc ON p.id = pc.product_id
                WHERE pc.cart_id = ?
                ORDER BY p.name
            """,
                (str(cart_id),),
            )

            rows = cursor.fetchall()
            return [self._row_to_model(dict(row)) for row in rows]

    async def get_carts_with_product(self, product_id: UUID) -> list[UUID]:
        """Get all carts containing a specific product."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT cart_id
                FROM product_cart
                WHERE product_id = ?
            """,
                (str(product_id),),
            )

            return [UUID(row[0]) for row in cursor.fetchall()]

    async def batch_add_to_cart(self, product_ids: list[UUID], cart_id: UUID) -> int:
        """Add multiple products to cart at once."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()

            # Подготавливаем данные для batch insert
            data = [(str(pid), str(cart_id)) for pid in product_ids]

            try:
                await cursor.executemany(
                    """
                    INSERT OR IGNORE INTO product_cart (product_id, cart_id)
                    VALUES (?, ?)
                """,
                    data,
                )

                added_count = cursor.rowcount
                logger.debug(f"Added {added_count} products to cart {cart_id}")
                return int(added_count)
            except sqlite3.Error as e:
                logger.error(f"Error in batch add to cart: {e}")
                return 0
