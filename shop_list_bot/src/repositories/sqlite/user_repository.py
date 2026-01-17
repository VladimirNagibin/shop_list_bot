"""Async SQLite implementation of user repository."""

import sqlite3

from uuid import UUID

from core.logger import logger
from interfaces.databases.user_interface import IUserRepository
from schemas.models import UserCreate, UserInDB, UserUpdate

from .base import SQLiteBaseRepository


class SQLiteUserRepository(
    SQLiteBaseRepository[UserInDB, UserCreate, UserUpdate], IUserRepository
):
    """Async SQLite implementation of user repository."""

    def __init__(self) -> None:
        super().__init__("users", UserInDB)

    async def get_by_tg_id(self, tg_id: int) -> UserInDB | None:
        """Get user by Telegram ID asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM users WHERE user_tg_id = ?", (tg_id,))
            row = await cursor.fetchone()

            if row:
                return self._row_to_model(dict(row))
            return None

    async def get_by_username(self, username: str) -> UserInDB | None:
        """Get user by username asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = await cursor.fetchone()

            if row:
                return self._row_to_model(dict(row))
            return None

    async def search_by_name(self, name_query: str) -> list[UserInDB]:
        """Search users by first name asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                "SELECT * FROM users WHERE first_name LIKE ? ORDER BY first_name",
                (f"%{name_query}%",),
            )
            rows = await cursor.fetchall()

            return [self._row_to_model(dict(row)) for row in rows]

    async def get_users_in_cart(self, cart_id: UUID) -> list[UserInDB]:
        """Get all users in a specific cart asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()
            await cursor.execute(
                """
                SELECT u.* FROM users u
                JOIN user_cart uc ON u.id = uc.user_id
                WHERE uc.cart_id = ?
                ORDER BY u.first_name
            """,
                (str(cart_id),),
            )

            rows = await cursor.fetchall()
            return [self._row_to_model(dict(row)) for row in rows]

    async def create_or_update_by_tg_id(self, tg_id: int, data: UserCreate) -> UserInDB:
        """Create or update user by Telegram ID asynchronously."""
        existing = await self.get_by_tg_id(tg_id)

        if existing:
            # Обновляем существующего пользователя
            updated = await self.update(existing.id, data)
            if updated:
                return updated
            else:
                return existing

        # Создаем нового пользователя
        created = await self.create(data)
        if not created:
            error_message = f"Failed to create user with tg_id {tg_id}"
            raise ValueError(error_message)
        return created

    async def get_with_carts(self, user_id: UUID) -> UserInDB | None:
        """Get user with their carts (eager loading) asynchronously."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Здесь можно добавить логику eager loading
        # Пока возвращаем пользователя без корзин
        return user

    async def bulk_create(self, users_data: list[UserCreate]) -> list[UserInDB]:
        """Create multiple users asynchronously."""
        if not users_data:
            return []

        db_manager = await self._get_db_manager()

        created_users: list[UserInDB] = []
        async with db_manager.get_connection() as conn:
            cursor = await conn.cursor()

            for user_data in users_data:
                try:
                    data_dict = user_data.model_dump()

                    if "id" not in data_dict or not data_dict["id"]:
                        from uuid import uuid4

                        data_dict["id"] = str(uuid4())

                    columns = ", ".join(data_dict.keys())
                    placeholders = ", ".join(["?" for _ in data_dict])
                    values = list(data_dict.values())

                    query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"  # nosec # noqa: S608
                    await cursor.execute(query, values)

                    # Получаем созданного пользователя
                    await cursor.execute(
                        "SELECT * FROM users WHERE id = ?", (data_dict["id"],)
                    )
                    row = await cursor.fetchone()
                    if row:
                        created_users.append(self._row_to_model(dict(row)))

                except sqlite3.Error as e:
                    logger.error(f"Error creating user in bulk: {e}")
                    continue

            await conn.commit()

        return created_users
