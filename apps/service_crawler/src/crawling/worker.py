import asyncio
from collections.abc import Iterable
from contextlib import suppress
import datetime as dt
from itertools import cycle

from aiohttp import ClientSession

from common.logs import LoggerLike
from service_crawler.src.crawling.models import CrawledURL


class Worker:
    def __init__(self, urls: Iterable[str], logger: LoggerLike, queue: asyncio.Queue[CrawledURL]) -> None:
        self._urls_to_crawl = set(urls)
        self._queue = queue
        self._logger = logger
        self._session = ClientSession()  # TODO: upgrade
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            for url in cycle(self._urls_to_crawl):
                crawled_url = await self._crawl(url)
                await self._queue.put(crawled_url)

    async def _crawl(self, url: str) -> CrawledURL:
        try:
            async with self._session.get(url, timeout=10) as response:
                result = CrawledURL(
                    url=url,
                    status="UP" if response.status < 400 else "DOWN",
                    updated_at=dt.datetime.now(tz=dt.UTC).isoformat(),
                )
        except Exception as error:
            self._logger.error("Error while crawling URL '%s': %s", url, error)
            result = CrawledURL(
                url=url,
                status="DOWN",
                updated_at=dt.datetime.now(tz=dt.UTC).isoformat(),
            )

        await asyncio.sleep(1)  # TODO: remove
        return result

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()
