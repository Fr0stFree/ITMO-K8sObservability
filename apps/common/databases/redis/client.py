from contextlib import suppress

from redis.asyncio import Redis

from common.databases.redis.settings import RedisClientSettings
from common.logs import LoggerLike


class RedisClient:
    def __init__(self, settings: RedisClientSettings, logger: LoggerLike) -> None:
        self._settings = settings
        self._logger = logger
        self._client = Redis.from_url(
            settings.dsn,
            db=settings.db,
            decode_responses=settings.decode_responses,
        )

    async def start(self) -> None:
        self._logger.info("Connecting to redis at %s:%s...", self._settings.host, self._settings.port)
        await self._client.ping()

    async def stop(self) -> None:
        self._logger.info("Shutting down the redis client...")
        if self._client:
            try:
                await self._client.close()
            finally:
                with suppress(Exception):
                    await self._client.connection_pool.disconnect()

    async def is_healthy(self) -> bool:
        return await self._client.ping()

    @property
    def redis(self) -> Redis:
        return self._client
