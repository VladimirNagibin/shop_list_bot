"""Base async SQLite repository implementation."""

import datetime
import sqlite3

from contextlib import suppress
from typing import Any, TypeVar, cast
from uuid import UUID, uuid4

from db import AsyncDatabaseFactory, DatabaseType
from interfaces.databases.base import IDatabaseManager, IRepository

from core.logger import logger

from .exeptions import InvalidFilterKeyError


T = TypeVar("T")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


class SQLiteBaseRepository(IRepository[T, CreateSchema, UpdateSchema]):
    """Base async SQLite repository implementation."""

    def __init__(self, table_name: str, model_class: type[T]):
        self.table_name = table_name
        self.model_class = model_class
        self._db_manager: IDatabaseManager | None = None

    async def _get_db_manager(self) -> IDatabaseManager:
        """Lazy initialization of database manager."""
        if self._db_manager is None:
            self._db_manager = await AsyncDatabaseFactory.get_manager(
                DatabaseType.SQLITE
            )
        return self._db_manager

    def _row_to_model(self, row: dict[str, Any]) -> T:
        """Convert database row to model instance."""
        for key, value in row.items():
            if (
                (key.endswith("_id") or key == "id")
                and value
                and isinstance(value, str)
            ):
                with suppress(ValueError):
                    row[key] = UUID(value)
            elif key.endswith("_at") and value and isinstance(value, str):
                with suppress(ValueError):
                    clean_date_str = value.replace("Z", "+00:00")
                    row[key] = datetime.datetime.fromisoformat(clean_date_str)

        return self.model_class(**row)

    async def create(self, data: CreateSchema) -> T | None:
        """Create a new record asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()

                dump_method = getattr(data, "model_dump", None)

                if callable(dump_method):
                    raw_dict = dump_method()
                else:
                    raw_dict = cast("dict[str, Any]", data)

                if not isinstance(raw_dict, dict):
                    logger.error(
                        f"Invalid data type provided for database record: {type(data)}"
                    )
                    return None

                data_dict = cast("dict[str, Any]", raw_dict)

                if "id" not in data_dict or not data_dict["id"]:
                    data_dict["id"] = str(uuid4())

                if "created_at" not in data_dict:
                    data_dict["created_at"] = datetime.datetime.now(
                        datetime.UTC
                    ).isoformat()

                valid_columns = self._get_valid_columns(data_dict)

                values = [data_dict[col] for col in valid_columns]

                columns = ", ".join(valid_columns)
                placeholders = ", ".join(["?" for _ in valid_columns])

                query = (
                    f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"  # nosec # noqa: S608
                )
                await cursor.execute(query, values)
                await conn.commit()
                logger.debug(
                    f"Created record in {self.table_name} with id: {data_dict['id']}"
                )
                return await self.get_by_id(UUID(data_dict["id"]))
            except sqlite3.Error as e:
                logger.error(f"Error creating record: {e}")
                await conn.rollback()
                return None
            except ValueError as e:
                logger.error(f"Data validation error: {e}")
                raise  # Пробрасываем ошибку валидации выше, так как это ошибка разраба

    def _get_valid_columns(self, data: dict[str, Any]) -> list[str]:
        """
        Извлекает валидные колонки из словаря данных.
        Выбрасывает ValueError, если встречаются невалидные ключи.
        """
        # Фильтруем ключи, оставляя только строки и валидные идентификаторы
        valid_columns = [k for k in data if k.isidentifier()]

        # Проверяем, что все ключи прошли валидацию
        if len(valid_columns) != len(data):
            error_message = (
                "Invalid keys in data dictionary. Keys must be valid identifiers."
            )
            raise ValueError(error_message)

        return valid_columns

    async def get_by_id(self, record_id: UUID) -> T | None:
        """Get record by ID asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()
                await cursor.execute(
                    f"SELECT * FROM {self.table_name} WHERE id = ?",  # nosec # noqa: S608
                    (str(record_id),),
                )
                row = await cursor.fetchone()

                if row:
                    return self._row_to_model(dict(row))
            except sqlite3.Error as e:
                logger.error(f"Error fetching record {record_id}: {e}")
                return None
            return None

    async def get_all(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[T]:
        """Get all records with pagination and filtering asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()
                query = f"SELECT * FROM {self.table_name}"  # nosec # noqa: S608
                params: list[Any] = []
                conditions: list[str] = []

                if filters:
                    for key, value in filters.items():
                        self._validate_filter_key(key)
                        conditions.append(f"{key} = ?")
                        params.append(value)
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)

                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, skip])

                await cursor.execute(query, params)
                rows = await cursor.fetchall()

                return [self._row_to_model(dict(row)) for row in rows]
            except sqlite3.Error as e:
                logger.error(f"Error fetching all records: {e}")
                return []
            except InvalidFilterKeyError as e:
                logger.error(e)
                raise

    def _validate_filter_key(self, key: str) -> None:
        """
        Проверяет, является ли ключ валидным SQL идентификатором.
        Вызывает исключение, если нет.
        """
        if not key.isidentifier():
            raise InvalidFilterKeyError(key)

    async def update(self, record_id: UUID, data: UpdateSchema) -> T | None:
        """Update a record asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()

                dump_method = getattr(data, "model_dump", None)

                if callable(dump_method):
                    raw_dict = dump_method(exclude_unset=True, exclude_none=True)
                else:
                    raw_dict = {
                        k: v
                        for k, v in cast("dict[str, Any]", data).items()
                        if v is not None
                    }

                if not isinstance(raw_dict, dict):
                    logger.error(
                        f"Invalid data type provided for database record: {type(data)}"
                    )
                    return None

                data_dict = cast("dict[str, Any]", raw_dict)

                if not data_dict:
                    logger.warning(f"No data provided for update of record {record_id}")
                    return await self.get_by_id(record_id)

                data_dict["updated_at"] = datetime.datetime.now(
                    datetime.UTC
                ).isoformat()

                set_clause = ", ".join([f"{key} = ?" for key in data_dict])
                values = list(data_dict.values())
                values.append(str(record_id))

                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"  # nosec # noqa: S608

                await cursor.execute(query, values)
                await conn.commit()

                if cursor.rowcount > 0:
                    logger.debug(f"Updated record {record_id} in {self.table_name}")
                    return await self.get_by_id(record_id)
            except sqlite3.Error as e:
                logger.error(f"Error updating record {record_id}: {e}")
                await conn.rollback()
                return None
            else:
                return None

    async def delete(self, record_id: UUID) -> bool:
        """Delete a record asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()
                await cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE id = ?",  # nosec # noqa: S608
                    (str(record_id),),
                )
                await conn.commit()

                if cursor.rowcount > 0:
                    logger.debug(f"Deleted record {record_id} from {self.table_name}")
                    return True
            except sqlite3.Error as e:
                logger.error(f"Error deleting record {record_id}: {e}")
                await conn.rollback()
                return False
            else:
                return False

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count records with optional filtering asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()
                query = f"SELECT COUNT(*) FROM {self.table_name}"  # nosec # noqa: S608
                params: list[Any] = []
                conditions: list[str] = []

                if filters:
                    for key, value in filters.items():
                        self._validate_filter_key(key)
                        conditions.append(f"{key} = ?")
                        params.append(value)
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)

                await cursor.execute(query, params)
                result = await cursor.fetchone()
                return int(result[0])
            except sqlite3.Error as e:
                logger.error(f"Error counting records: {e}")
                return 0
            except InvalidFilterKeyError as e:
                logger.error(e)
                raise

    async def exists(self, record_id: UUID) -> bool:
        """Check if record exists asynchronously."""
        db_manager = await self._get_db_manager()

        async with db_manager.get_connection() as conn:
            try:
                cursor = await conn.cursor()
                await cursor.execute(
                    f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1",  # nosec # noqa: S608
                    (str(record_id),),
                )
                result = await cursor.fetchone()
            except sqlite3.Error as e:
                logger.error(f"Error checking existence of record {record_id}: {e}")
                return False
            else:
                return result is not None
