import asyncio
from contextlib import suppress
from common.logs.logger import LoggerLike
from service_crawler.src.models import CrawledURL


class URLDumper:
    def __init__(self, queue: asyncio.Queue[CrawledURL], logger: LoggerLike) -> None:
        self._urls = queue
        self._logger = logger
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._logger.info("Starting URL dumper...")
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            crawled_url = await self._urls.get()
            self._logger.info("Dumped URL '%s' with status '%s'", crawled_url.url, crawled_url.status)
            self._urls.task_done()

    async def stop(self) -> None:
        self._logger.info("Stopping URL dumper...")
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
    
    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()