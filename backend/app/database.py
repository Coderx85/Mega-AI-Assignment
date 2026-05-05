from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class Database:
    def __init__(self, url: str):
        self._url = url
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self, **kwargs) -> AsyncEngine:
        self._engine = create_async_engine(self._url, **kwargs)
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
        )
        return self._engine

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()

    async def create_tables(self, base_class: type) -> None:
        if self._engine is None:
            raise RuntimeError("Database not initialized")
        async with self._engine.begin() as conn:
            await conn.run_sync(base_class.metadata.create_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._session_factory is None:
            raise RuntimeError("Database not initialized")
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
