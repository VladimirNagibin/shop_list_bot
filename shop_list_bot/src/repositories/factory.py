"""Async repository factory for creating implementations."""

from typing import Any, ClassVar, cast

from db import DatabaseType
from interfaces.databases.cart_interface import ICartRepository
from interfaces.databases.product_interface import IProductRepository
from interfaces.databases.user_interface import IUserRepository


ERROR_MESSAGE = "PostgreSQL repository not implemented yet"
StoredRepository = IUserRepository | IProductRepository | ICartRepository


class AsyncRepositoryFactory:
    """Factory for creating async repository instances."""

    _repositories: ClassVar[dict[tuple[str, DatabaseType], StoredRepository]] = {}

    @staticmethod
    async def get_user_repository(
        repo_type: DatabaseType = DatabaseType.SQLITE, **kwargs: Any
    ) -> IUserRepository:
        """Get async user repository instance."""
        key = ("user", repo_type)

        if key not in AsyncRepositoryFactory._repositories:
            if repo_type == DatabaseType.SQLITE:
                from .sqlite.user_repository import SQLiteUserRepository

                instance = SQLiteUserRepository(**kwargs)
            elif repo_type == DatabaseType.POSTGRESQL:
                raise NotImplementedError(ERROR_MESSAGE)
            else:
                error_message = f"Unsupported repository type: {repo_type}"
                raise ValueError(error_message)

            AsyncRepositoryFactory._repositories[key] = instance

        return cast("IUserRepository", AsyncRepositoryFactory._repositories[key])

    @staticmethod
    async def get_cart_repository(
        repo_type: DatabaseType = DatabaseType.SQLITE, **kwargs: Any
    ) -> ICartRepository:
        """Get async cart repository instance."""
        key = ("cart", repo_type)

        if key not in AsyncRepositoryFactory._repositories:
            if repo_type == DatabaseType.SQLITE:
                from .sqlite.cart_repository import SQLiteCartRepository

                instance = SQLiteCartRepository(**kwargs)
            elif repo_type == DatabaseType.POSTGRESQL:
                raise NotImplementedError(ERROR_MESSAGE)
            else:
                error_message = f"Unsupported repository type: {repo_type}"
                raise ValueError(error_message)

            AsyncRepositoryFactory._repositories[key] = instance

        return cast("ICartRepository", AsyncRepositoryFactory._repositories[key])

    @staticmethod
    async def get_product_repository(
        repo_type: DatabaseType = DatabaseType.SQLITE, **kwargs: Any
    ) -> IProductRepository:
        """Get async product repository instance."""
        key = ("product", repo_type)

        if key not in AsyncRepositoryFactory._repositories:
            if repo_type == DatabaseType.SQLITE:
                from .sqlite.product_repository import SQLiteProductRepository

                instance = SQLiteProductRepository(**kwargs)
            elif repo_type == DatabaseType.POSTGRESQL:
                raise NotImplementedError(ERROR_MESSAGE)
            else:
                error_message = f"Unsupported repository type: {repo_type}"
                raise ValueError(error_message)

            AsyncRepositoryFactory._repositories[key] = instance

        return cast("IProductRepository", AsyncRepositoryFactory._repositories[key])

    @staticmethod
    def clear_cache() -> None:
        """Clear repository cache."""
        AsyncRepositoryFactory._repositories.clear()

    @staticmethod
    async def close_all() -> None:
        """Close all repository connections."""
        AsyncRepositoryFactory.clear_cache()
