import asyncio
from collections.abc import Iterable, Sequence
from contextlib import suppress
import datetime as dt
from itertools import cycle

from aiohttp import ClientSession

from common.logs.logger import LoggerLike
from service_crawler.src.crawling.models import CrawledURL


class WorkerPool:
    def __init__(
        self,
        amount: int,
        urls: Sequence[str],
        queue: asyncio.Queue,
        logger: LoggerLike,
    ) -> None:
        urls_per_crawler = len(urls) // amount
        self._amount = amount
        self._logger = logger
        self._crawlers = [
            Worker(
                urls=list(urls[i : i + urls_per_crawler]),
                logger=logger,
                results=queue,
            )
            for i in range(0, len(urls), urls_per_crawler)
        ]

    @property
    def amount(self) -> int:
        return self._amount

    async def start(self) -> None:
        for crawler in self._crawlers:
            asyncio.create_task(crawler.start())

    async def stop(self) -> None:
        await asyncio.gather(*(crawler.stop() for crawler in self._crawlers))

    async def is_healthy(self) -> bool:
        results = await asyncio.gather(*(crawler.is_healthy() for crawler in self._crawlers))
        return all(results)


class Worker:
    def __init__(self, urls: Iterable[str], logger: LoggerLike, results: asyncio.Queue[CrawledURL]) -> None:
        self._urls_to_crawl = set(urls)
        self._results = results
        self._logger = logger
        self._session = ClientSession()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            for url in cycle(self._urls_to_crawl):
                crawled_url = await self._crawl(url)
                await self._results.put(crawled_url)

    async def _crawl(self, url: str) -> CrawledURL:
        try:
            async with self._session.get(url, timeout=10) as response:
                result = CrawledURL(
                    url=url,
                    status="UP" if response.status < 400 else "DOWN",
                    updated_at=dt.datetime.now(tz=dt.UTC),
                )
        except Exception as error:
            self._logger.error("Error while crawling URL '%s': %s", url, error)
            result = CrawledURL(
                url=url,
                status="DOWN",
                updated_at=dt.datetime.now(tz=dt.UTC),
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
