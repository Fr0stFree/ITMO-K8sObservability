from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from common.databases.postgres.settings import PostgresSettings
from common.logs import LoggerLike


class PostgresClient:
    def __init__(self, settings: PostgresSettings, logger: LoggerLike) -> None:
        self._logger = logger
        self._settings = settings
        self._engine = create_async_engine(
            settings.dsn,
            echo=settings.should_log_statements,
            future=True,
        )
        self._async_session = sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    async def start(self) -> None:
        self._logger.info("Connecting to db on %s:%s...", self._settings.host, self._settings.port)
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def stop(self) -> None:
        self._logger.info("Shutting down the postgres client...")
        await self._engine.dispose()

    async def is_healthy(self) -> bool:
        try:
            async with self._async_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._async_session() as session:
            yield session
            await session.commit()
