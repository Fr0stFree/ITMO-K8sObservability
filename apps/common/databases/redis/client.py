from contextlib import suppress

from redis.asyncio import Redis

from common.logs import LoggerLike


class RedisClient:
    def __init__(self, host: str, port: int, database: int, password: str, logger: LoggerLike) -> None:
        self._host = host
        self._port = port
        self._db = database
        self._logger = logger
        self._client = Redis.from_url(f"redis://:{password}@{host}:{port}/{database}", decode_responses=True)

    async def start(self) -> None:
        self._logger.info("Connecting to redis at %s:%s to database '%s'...", self._host, self._port, self._db)
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
