import asyncio
from collections.abc import Iterable
from contextlib import suppress
import datetime as dt
from http import HTTPMethod

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from bubus import EventBus
from dependency_injector.wiring import Provide, inject
from opentelemetry.trace import Tracer

from common.logs import LoggerLike
from service_crawler.src.container import Container
from service_crawler.src.crawling.const import REQUEST_HEADERS
from service_crawler.src.crawling.events import (
    WorkerCrawlCompletedEvent,
    WorkerCrawlFailedEvent,
    WorkerCrawlStartedEvent,
    WorkerIdleEvent,
)
from service_crawler.src.crawling.models import ResourceStatus


class Worker:

    @inject
    def __init__(
        self, worker_number: int, timeout: dt.timedelta = Provide[Container.settings.worker_request_timeout]
    ) -> None:
        self._urls_to_crawl = []
        self._unique_urls = set()
        self._session = ClientSession(
            timeout=ClientTimeout(total=timeout.total_seconds()),
            headers=REQUEST_HEADERS,
            connector=TCPConnector(verify_ssl=False),
        )
        self._task: asyncio.Task | None = None
        self._worker_id = worker_number
        self._current_index = 0

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        await self._session.close()

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()

    @inject
    def add_urls(
        self,
        urls: Iterable[str],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        new_urls = [url for url in urls if url not in self._unique_urls]
        self._urls_to_crawl.extend(new_urls)
        self._unique_urls.update(new_urls)
        logger.info(
            "Added %d new URL(s) to crawl: %s",
            len(new_urls),
            ", ".join(new_urls),
            extra={"urls": new_urls, "worker": self._worker_id},
        )

    @inject
    def remove_urls(
        self,
        urls: Iterable[str],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        to_remove = [url for url in urls if url in self._unique_urls]
        self._urls_to_crawl = [url for url in self._urls_to_crawl if url not in to_remove]
        self._unique_urls.difference_update(to_remove)
        logger.info(
            "Removed %d URL(s) from crawl list: %s",
            len(to_remove),
            to_remove,
            extra={"urls": to_remove, "worker": self._worker_id},
        )
        self._current_index = 0

    @inject
    async def _run(
        self,
        bus: EventBus = Provide[Container.event_bus],
        tracer: Tracer = Provide[Container.tracer],
    ) -> None:
        while True:
            url = self.__get_next_url()
            if url is None:
                await bus.dispatch(WorkerIdleEvent(worker_id=self._worker_id))
                await asyncio.sleep(5)
                continue

            span = tracer.start_span("crawl.url")
            method = HTTPMethod.GET
            event = WorkerCrawlStartedEvent(worker_id=self._worker_id, url=url, method=method, span=span)
            await bus.dispatch(event)

            try:
                async with self._session.get(url) as response:
                    status = ResourceStatus.UP if response.status < 400 else ResourceStatus.DOWN

                event = WorkerCrawlCompletedEvent(
                    worker_id=self._worker_id, span=span, status=status, method=method, url=url
                )
            except Exception as error:
                event = WorkerCrawlFailedEvent(
                    worker_id=self._worker_id, url=url, method=method, error=error, span=span
                )

            await bus.dispatch(event)
            await asyncio.sleep(2)

    def __get_next_url(self) -> str | None:
        if not self._urls_to_crawl:
            return None

        url = self._urls_to_crawl[self._current_index % len(self._urls_to_crawl)]
        self._current_index += 1
        return url
