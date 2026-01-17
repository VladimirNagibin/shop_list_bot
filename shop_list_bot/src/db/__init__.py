"""Async database factory and connection managers."""

import asyncio

from enum import Enum
from typing import Any, ClassVar

from core.logger import logger
from core.settings import settings
from interfaces.databases.base import IDatabaseManager


class DatabaseType(Enum):
    """Supported database types."""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"


class AsyncDatabaseFactory:
    """Factory for creating async database managers."""

    _instances: ClassVar[dict[tuple[DatabaseType, str | None], IDatabaseManager]] = {}
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @staticmethod
    async def get_manager(
        db_type: DatabaseType = DatabaseType.SQLITE,
        connection_string: str | None = None,
        **kwargs: Any,
    ) -> IDatabaseManager:
        """Get async database manager instance."""
        key = (db_type, connection_string)

        if key not in AsyncDatabaseFactory._instances:
            async with AsyncDatabaseFactory._lock:
                if key not in AsyncDatabaseFactory._instances:
                    if db_type == DatabaseType.SQLITE:
                        from .sqlite_manager import SQLiteManager

                        conn_str = connection_string or settings.DB_SQLITE_PATH
                        manager: IDatabaseManager = SQLiteManager(conn_str, **kwargs)

                    elif db_type == DatabaseType.POSTGRESQL:
                        from .postgres_manager import PostgreSQLManager

                        if not connection_string:
                            erroor_message = (
                                "PostgreSQL requires a connection string. "
                                "Example: 'postgresql://user:password@localhost/dbname'"
                            )
                            raise ValueError(erroor_message)

                        manager = PostgreSQLManager(connection_string, **kwargs)

                    else:
                        error_message = f"Unsupported database type: {db_type}"
                        raise ValueError(error_message)
                    await manager.initialize()
                    AsyncDatabaseFactory._instances[key] = manager

        return AsyncDatabaseFactory._instances[key]

    @staticmethod
    async def close_all() -> None:
        """Close all database connections."""
        managers = list(AsyncDatabaseFactory._instances.values())
        for manager in managers:
            try:
                await manager.close()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error closing database manager: {e}")
        AsyncDatabaseFactory._instances.clear()
