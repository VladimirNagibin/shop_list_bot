"""Main application with async dependency injection."""

import asyncio
import datetime
import sys

from typing import TYPE_CHECKING, Any

from core.logger import logger
from db import DatabaseType
from interfaces.databases.cart_interface import ICartRepository
from interfaces.databases.product_interface import IProductRepository
from interfaces.databases.user_interface import IUserRepository
from repositories.factory import AsyncRepositoryFactory
from schemas.models import (
    CartCreate,
    ProductCreate,
    UserCreate,
    UserUpdate,
)


if TYPE_CHECKING:
    from collections.abc import Coroutine

    from schemas.models import ProductInDB, UserInDB


async def example_user_operations(user_repo: IUserRepository) -> None:
    """Пример асинхронных операций с пользователями."""
    print("\n=== Пример асинхронных операций с пользователями ===")

    # Создание пользователя
    user_data = UserCreate(
        username="async_user", first_name="Async", user_tg_id=123456789
    )

    created_user = await user_repo.create(user_data)
    if created_user:
        print(
            f"1. Создан пользователь: {created_user.first_name} "
            f"({created_user.username})"
        )

    # Получение пользователя по Telegram ID
    user_by_tg = await user_repo.get_by_tg_id(123456789)
    print(
        "2. Найден по Telegram ID: "
        f"{user_by_tg.username if user_by_tg else 'Не найден'}"
    )

    # Поиск по имени
    users = await user_repo.search_by_name("Async")
    print(f"3. Найдено пользователей по имени: {len(users)}")

    # Обновление пользователя
    if created_user:
        update_dat = {"first_name": "Async Updated"}
        update_data = UserUpdate(**update_dat)
        updated = await user_repo.update(created_user.id, update_data)
        print(
            f"4. Обновлен пользователь: {updated.first_name if updated else 'Ошибка'}"
        )

    # Создание или обновление
    user_data2 = UserCreate(
        username="tg_user_999", first_name="Telegram", user_tg_id=999999999
    )

    user = await user_repo.create_or_update_by_tg_id(999999999, user_data2)
    print(f"5. Создан/обновлен пользователь: {user.first_name}")

    # Проверка существования
    exists = await user_repo.exists(created_user.id) if created_user else False
    print(f"6. Пользователь существует: {exists}")

    # Количество пользователей
    count = await user_repo.count()
    print(f"7. Всего пользователей: {count}")


async def example_cart_operations(
    cart_repo: ICartRepository, user_repo: IUserRepository
) -> None:
    """Пример асинхронных операций с корзинами."""
    print("\n=== Пример асинхронных операций с корзинами ===")

    # Получаем или создаем тестового пользователя
    user_data = UserCreate(
        username="cart_owner", first_name="Owner", user_tg_id=111111111
    )
    owner = await user_repo.create_or_update_by_tg_id(111111111, user_data)

    # Создаем корзину с владельцем
    cart_data = CartCreate(
        name="Моя первая корзина", created_at=datetime.datetime.now(datetime.UTC)
    )

    cart = await cart_repo.create_cart_with_owner(cart_data, owner.id)
    print(f"1. Создана корзина: {cart.name if cart else 'Ошибка'}")

    if cart:
        # Добавляем еще одного пользователя в корзину
        user_data2 = UserCreate(
            username="cart_member", first_name="Member", user_tg_id=222222222
        )
        member = await user_repo.create_or_update_by_tg_id(222222222, user_data2)

        added = await cart_repo.add_user_to_cart(member.id, cart.id, "editor")
        print(f"2. Добавлен пользователь в корзину: {added}")

        # Получаем пользователей корзины
        cart_users = await cart_repo.get_cart_users(cart.id)
        print(f"3. Пользователей в корзине: {len(cart_users)}")

        # Получаем владельца корзины
        owner_id = await cart_repo.get_cart_owner(cart.id)
        print(f"4. Владелец корзины: {owner_id}")


async def example_product_operations(
    product_repo: IProductRepository, cart_repo: ICartRepository
) -> None:
    """Пример асинхронных операций с продуктами."""
    print("\n=== Пример асинхронных операций с продуктами ===")

    # Создаем несколько продуктов
    products_data = [
        ProductCreate(name="Молоко", price=89.90),
        ProductCreate(name="Хлеб", price=45.50),
        ProductCreate(name="Яйца", price=120.00),
        ProductCreate(name="Сыр", price=350.00),
    ]

    created_products: list[ProductInDB] = []
    for product_data in products_data:
        product = await product_repo.create(product_data)
        if product:
            created_products.append(product)
            print(f"Создан продукт: {product.name} - {product.price} руб.")

    # Поиск продуктов
    found_products = await product_repo.search_by_name("сыр")
    print(f"\nНайдено продуктов по запросу 'сыр': {len(found_products)}")

    # Добавляем продукты в корзину (если есть)
    carts = await cart_repo.get_all(limit=1)
    if carts and created_products:
        cart = carts[0]
        added_count = await product_repo.batch_add_to_cart(
            [p.id for p in created_products[:2]], cart.id
        )
        print(f"\nДобавлено продуктов в корзину: {added_count}")

        # Получаем продукты в корзине
        cart_products = await product_repo.get_products_in_cart(cart.id)
        print(f"Продуктов в корзине: {len(cart_products)}")


async def performance_example(user_repo: IUserRepository) -> None:
    """Пример асинхронной производительности."""
    print("\n=== Тест асинхронной производительности ===")

    import time

    # Создаем несколько пользователей параллельно
    start_time = time.time()

    tasks: list[Coroutine[Any, Any, UserInDB | None]] = []
    for i in range(5):
        user_data = UserCreate(
            username=f"test_user_{i}", first_name=f"Test_{i}", user_tg_id=1000000000 + i
        )
        tasks.append(user_repo.create(user_data))

    # Запускаем все задачи параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    print(f"Создано 5 пользователей за: {end_time - start_time:.2f} секунд")
    print(f"Успешно создано: {sum(1 for r in results if r is not None)}")


async def main() -> None:
    """Главная асинхронная функция."""
    print("=== Использование асинхронных интерфейсов и фабрики ===\n")

    try:
        # Получаем асинхронные репозитории через фабрику
        user_repo = await AsyncRepositoryFactory.get_user_repository(
            DatabaseType.SQLITE
        )
        cart_repo = await AsyncRepositoryFactory.get_cart_repository(
            DatabaseType.SQLITE
        )
        product_repo = await AsyncRepositoryFactory.get_product_repository(
            DatabaseType.SQLITE
        )

        # Проверяем типы
        print("Типы асинхронных репозиториев:")
        print(f"User repo: {type(user_repo).__name__}")
        print(f"Cart repo: {type(cart_repo).__name__}")
        print(f"Product repo: {type(product_repo).__name__}")

        # Выполняем примеры операций
        await example_user_operations(user_repo)
        await example_cart_operations(cart_repo, user_repo)
        await example_product_operations(product_repo, cart_repo)
        await performance_example(user_repo)

        print("\n=== Все операции завершены успешно ===")
    except (ConnectionError, TimeoutError) as e:
        # Ошибки соединения с БД
        logger.error(f"Ошибка подключения к базе данных: {e}")
        print("Проверьте подключение к базе данных и попробуйте снова")
        sys.exit(1)

    except ValueError as e:
        # Ошибки валидации данных
        logger.error(f"Ошибка в данных: {e}")
        print(f"Ошибка в данных: {e}")

    except RuntimeError as e:
        # Ошибки времени выполнения
        logger.error(f"Ошибка выполнения: {e}", exc_info=True)
        print("Произошла ошибка во время выполнения операций")

    except ImportError as e:
        # Ошибки импорта модулей
        logger.error(f"Ошибка импорта: {e}")
        print("Проверьте установленные зависимости: pip install -r requirements.txt")
        sys.exit(1)

    except KeyboardInterrupt:
        # Пользователь прервал выполнение (Ctrl+C)
        logger.info("Программа прервана пользователем")
        print("\nПрограмма прервана пользователем")

    finally:
        # Закрываем все соединения
        try:
            await AsyncRepositoryFactory.close_all()

            from db import AsyncDatabaseFactory

            await AsyncDatabaseFactory.close_all()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Ошибка при закрытии соединений: {e}")


if __name__ == "__main__":
    # Запускаем асинхронную главную функцию
    asyncio.run(main())
