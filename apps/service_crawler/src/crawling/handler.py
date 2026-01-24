import asyncio
from contextlib import suppress
from typing import Protocol

from common.logs.logger import LoggerLike
from service_crawler.src.crawling.models import CrawledURL


class OnURLCrawledCallback(Protocol):
    async def __call__(self, url: CrawledURL) -> None: ...


class Handler:
    def __init__(
        self,
        queue: asyncio.Queue[CrawledURL],
        on_url_crawled: OnURLCrawledCallback,
        logger: LoggerLike,
    ) -> None:
        self._urls = queue
        self._logger = logger
        self._callback = on_url_crawled
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            crawled_url = await self._urls.get()
            await self._callback(crawled_url)
            self._urls.task_done()

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()
