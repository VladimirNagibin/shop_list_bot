"""SQLite implementation of cart repository."""

import sqlite3

from uuid import UUID

from core.logger import logger
from interfaces.databases.cart_interface import ICartRepository
from schemas.models import CartCreate, CartInDB, CartUpdate

from .base_sqlite import SQLiteBaseRepository


class SQLiteCartRepository(
    SQLiteBaseRepository[CartInDB, CartCreate, CartUpdate], ICartRepository
):
    """SQLite implementation of cart repository."""

    def __init__(self) -> None:
        super().__init__("carts", CartInDB)

    async def get_carts_by_user(self, user_id: UUID) -> list[tuple[CartInDB, str]]:
        """Get all carts for a user with their roles."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT c.*, uc.role
                FROM carts c
                JOIN user_cart uc ON c.id = uc.cart_id
                WHERE uc.user_id = ?
                ORDER BY c.created_at DESC
            """,
                (str(user_id),),
            )

            results: list[tuple[CartInDB, str]] = []
            for row in await cursor.fetchall():
                cart_data = dict(row)
                role = cart_data.pop("role")
                cart = self._row_to_model(cart_data)
                results.append((cart, role))

            return results

    async def add_user_to_cart(
        self, user_id: UUID, cart_id: UUID, role: str = "viewer"
    ) -> bool:
        """Add user to cart with specified role."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            try:
                await cursor.execute(
                    """
                    INSERT OR REPLACE INTO user_cart (user_id, cart_id, role)
                    VALUES (?, ?, ?)
                """,
                    (str(user_id), str(cart_id), role),
                )
                logger.debug(f"Added user {user_id} to cart {cart_id} with role {role}")
            except sqlite3.Error as e:
                logger.error(f"Error adding user to cart: {e}")
                return False
            else:
                return True

    async def remove_user_from_cart(self, user_id: UUID, cart_id: UUID) -> bool:
        """Remove user from cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                DELETE FROM user_cart WHERE user_id = ? AND cart_id = ?
                """,
                (str(user_id), str(cart_id)),
            )

            if cursor.rowcount > 0:
                logger.debug(f"Removed user {user_id} from cart {cart_id}")
                return True
            return False

    async def update_user_role(self, user_id: UUID, cart_id: UUID, role: str) -> bool:
        """Update user's role in cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                UPDATE user_cart SET role = ? WHERE user_id = ? AND cart_id = ?
            """,
                (role, str(user_id), str(cart_id)),
            )

            if cursor.rowcount > 0:
                logger.debug(f"Updated user {user_id} role to {role} in cart {cart_id}")
                return True
            return False

    async def get_cart_users(self, cart_id: UUID) -> list[tuple[UUID, str]]:
        """Get all users in a cart with their roles."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT user_id, role FROM user_cart WHERE cart_id = ?
                ORDER BY role, created_at
            """,
                (str(cart_id),),
            )

            return [(UUID(row[0]), row[1]) for row in cursor.fetchall()]

    async def get_cart_owner(self, cart_id: UUID) -> UUID | None:
        """Get the owner of a cart."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT user_id
                FROM user_cart
                WHERE cart_id = ? AND role = 'owner'
                LIMIT 1
            """,
                (str(cart_id),),
            )

            row = cursor.fetchone()
            return UUID(row[0]) if row else None

    async def create_cart_with_owner(
        self, data: CartCreate, owner_id: UUID
    ) -> CartInDB | None:
        """Create a cart and assign an owner."""
        # Используем транзакцию для атомарности
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()

                # Создаем корзину
                cart_id = str(data.id) if hasattr(data, "id") and data.id else None
                if not cart_id:
                    from uuid import uuid4

                    cart_id = str(uuid4())

                await cursor.execute(
                    """
                    INSERT INTO carts (id, name, created_at)
                    VALUES (?, ?, ?)
                """,
                    (
                        cart_id,
                        data.name,
                        data.created_at.isoformat()
                        if hasattr(data, "created_at")
                        else None,
                    ),
                )

                # Добавляем владельца
                await cursor.execute(
                    """
                    INSERT INTO user_cart (user_id, cart_id, role)
                    VALUES (?, ?, 'owner')
                """,
                    (str(owner_id), cart_id),
                )

                logger.debug(f"Created cart {cart_id} with owner {owner_id}")
                return await self.get_by_id(UUID(cart_id))

            except sqlite3.Error as e:
                logger.error(f"Error creating cart with owner: {e}")
                conn.rollback()
                return None

    async def get_with_products(self, cart_id: UUID) -> CartInDB | None:
        """Get cart with all products (eager loading)."""
        cart = await self.get_by_id(cart_id)
        # В реальной реализации нужно будет добавить eager loading продуктов
        return cart

    async def get_with_users_and_products(self, cart_id: UUID) -> CartInDB | None:
        """Get cart with users and products (full eager loading)."""
        cart = await self.get_by_id(cart_id)
        # В реальной реализации нужно будет добавить eager loading
        return cart
