"""Инициализация подключения к базе данных."""
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.repository.database.models.models import Base


class AsyncDBEngine:
    """Класс для работы с асинхронным движком БД."""

    def __init__(self, db_settings: dict[str, Any]):
        self.engine: AsyncEngine = create_async_engine(**db_settings)

    async def create_tables(self):
        """Проверяет наличие таблиц в БД и создаёт отсутствующие."""
        # pylint: disable=locally-disabled, no-member
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close_connections(self):
        """Закрывает активные соединения с БД."""
        await self.engine.dispose()


async_engine = AsyncDBEngine(settings.engine_config)

# expire_on_commit=False will prevent attributes from being expired
# after commit.
async_session = sessionmaker(
    async_engine.engine,
    expire_on_commit=False,
    class_=AsyncSession,
    future=True,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Генерирует новый объект сессии базы данных.

    По завершении работы с ним - закрывает.
    """
    async with async_session() as session:
        yield session
