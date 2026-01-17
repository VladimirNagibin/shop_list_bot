"""Async PostgreSQL database manager (stub for future implementation)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from interfaces.databases.base import IDatabaseManager

from core.logger import logger


class PostgreSQLManager(IDatabaseManager):
    """Async PostgreSQL database manager (stub)."""

    ERROR_MESSAGE = "PostgreSQL not implemented yet"

    def __init__(self, connection_string: str, **kwargs: Any):
        self.connection_string = connection_string
        logger.warning("PostgreSQL async implementation is not yet available")

    async def initialize(self) -> None:
        """Initialize PostgreSQL connection pool."""

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[Any]:
        """Get database connection."""
        yield
        raise NotImplementedError(self.ERROR_MESSAGE)

    async def execute_query(
        self, query: str, params: tuple[Any] | None = None
    ) -> list[Any]:
        """Execute raw SQL query."""
        raise NotImplementedError(self.ERROR_MESSAGE)

    async def execute_many(self, query: str, params_list: list[Any]) -> None:
        """Execute many SQL statements."""
        raise NotImplementedError(self.ERROR_MESSAGE)

    async def backup(self, backup_path: str | None = None) -> bool:
        """Create database backup."""
        raise NotImplementedError(self.ERROR_MESSAGE)

    async def health_check(self) -> bool:
        """Check database health."""
        return False

    async def close(self) -> None:
        """Close all connections."""
