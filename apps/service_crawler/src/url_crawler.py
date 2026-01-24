import asyncio
from contextlib import suppress
from itertools import cycle
from typing import Iterable, Sequence
import datetime as dt

from aiohttp import ClientSession
from common.logs.logger import LoggerLike
from service_crawler.src.models import CrawledURL


class CrawlerPool:
    def __init__(
        self,
        amount: int,
        urls: Sequence[str],
        queue: asyncio.Queue,
        logger: LoggerLike,
    ) -> None:
        urls_per_crawler = len(urls) // amount
        self._logger = logger
        self._crawlers = [
            URLCrawler(
                urls=list(urls[i : i + urls_per_crawler]),
                logger=logger,
                results=queue,
            )
            for i in range(0, len(urls), urls_per_crawler)
        ]

    async def start(self) -> None:
        self._logger.info("Starting %d crawlers...", len(self._crawlers))
        for crawler in self._crawlers:
            asyncio.create_task(crawler.start())
        self._logger.info("Crawlers have been started")

    async def stop(self) -> None:
        self._logger.info("Stopping crawlers...")
        for crawler in self._crawlers:
            await crawler.stop()
        self._logger.info("Crawlers have been stopped")

    async def is_healthy(self) -> bool:
        results = await asyncio.gather(*(crawler.is_healthy() for crawler in self._crawlers))
        return all(results)


class URLCrawler:
    def __init__(self, urls: Iterable[str], logger: LoggerLike, results: asyncio.Queue[CrawledURL]) -> None:
        self._urls_to_crawl = set(urls)
        self._results = results
        self._logger = logger
        self._session = ClientSession()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._logger.info("Starting URL crawler...")
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
                    updated_at=dt.datetime.now(tz=dt.timezone.utc),
                )
        except Exception as error:
            self._logger.error("Error while crawling URL '%s': %s", url, error)
            result = CrawledURL(
                url=url,
                status="DOWN",
                updated_at=dt.datetime.now(tz=dt.timezone.utc),
            )

        await asyncio.sleep(1)
        return result

    async def stop(self) -> None:
        self._logger.info("Stopping URL crawler...")
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()
