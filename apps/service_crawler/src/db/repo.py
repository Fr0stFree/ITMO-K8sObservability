from typing import ClassVar

from dependency_injector.wiring import Provide, inject
from redis.asyncio import Redis

from service_crawler.src.container import Container


class Repository:
    TARGETS_SET_NAME: ClassVar[str] = "crawling_urls"

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def is_healthy(self) -> bool:
        return True

    @inject
    async def add_target(
        self,
        target: str,
        redis: Redis = Provide[Container.db_client.provided.redis],
    ) -> None:
        await redis.sadd(self.TARGETS_SET_NAME, target)

    @inject
    async def get_targets(
        self,
        redis: Redis = Provide[Container.db_client.provided.redis],
    ) -> set[str]:
        targets = await redis.smembers(self.TARGETS_SET_NAME)
        return targets

    @inject
    async def remove_target(
        self,
        target: str,
        redis: Redis = Provide[Container.db_client.provided.redis],
    ) -> None:
        await redis.srem(self.TARGETS_SET_NAME, target)
