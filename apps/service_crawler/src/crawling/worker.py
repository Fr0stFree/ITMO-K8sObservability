import asyncio
from collections.abc import Iterable
from contextlib import suppress
import datetime as dt
from http import HTTPMethod

from aiohttp import ClientSession, ClientTimeout
from dependency_injector.wiring import Provide, inject
from opentelemetry.propagate import inject as inject_context
from opentelemetry.trace import Tracer
from opentelemetry.trace.span import Span
from opentelemetry.trace.status import StatusCode
from prometheus_client import Counter

from common.logs import LoggerLike
from service_crawler.src.container import Container
from service_crawler.src.crawling.models import CrawledURL, ResourceStatus


class Worker:

    @inject
    def __init__(
        self,
        queue: asyncio.Queue,
        worker_number: int,
        timeout: dt.timedelta = Provide[Container.settings.worker_request_timeout],
    ) -> None:
        self._queue = queue
        self._urls_to_crawl = []
        self._unique_urls = set()
        self._session = ClientSession()  # TODO: upgrade
        self._task: asyncio.Task | None = None
        self._timeout = ClientTimeout(total=timeout.total_seconds())
        self._current_index = 0
        self._worker_number = worker_number

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
            extra={"urls": new_urls, "worker": self._worker_number},
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
            extra={"urls": to_remove, "worker": self._worker_number},
        )
        self._current_index = 0

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    @inject
    async def _run(
        self,
        tracer: Tracer = Provide[Container.tracer],
        counter: Counter = Provide[Container.crawled_urls_counter],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        while True:
            index = self._current_index % len(self._urls_to_crawl) if self._urls_to_crawl else 0
            url = self._urls_to_crawl[index] if self._urls_to_crawl else None
            if url is None:
                logger.warning("No URLs to crawl, worker is idling...", extra={"worker": self._worker_number})
                await asyncio.sleep(5)
                continue

            with tracer.start_as_current_span(
                "http.crawl",
                attributes={"http.url": url, "http.method": HTTPMethod.GET, "worker": self._worker_number},
            ):
                logger.info("Checking URL '%s'...", url, extra={"url": url, "worker": self._worker_number})
                url = await self._crawl(url)
                counter.labels(status=url.status).inc()
                meta = {}
                inject_context(meta)
                await self._queue.put((url, meta))
                self._current_index += 1

    @inject
    async def _crawl(
        self,
        url: str,
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> CrawledURL:
        try:
            async with self._session.get(url, timeout=self._timeout) as response:
                span.set_attribute("http.status_code", response.status)
                result = CrawledURL(
                    url=url,
                    status=ResourceStatus.UP if response.status < 400 else ResourceStatus.DOWN,
                    updated_at=dt.datetime.now(tz=dt.UTC).isoformat(),
                )
                span.set_status(StatusCode.OK)
        except Exception as error:
            logger.error("Error while crawling URL '%s': %s", url, error)
            result = CrawledURL(
                url=url,
                status=ResourceStatus.UNKNOWN,
                updated_at=dt.datetime.now(tz=dt.UTC).isoformat(),
                comment=str(error),
            )
            span.record_exception(error)
            span.set_status(StatusCode.ERROR)

        await asyncio.sleep(2)  # TODO: remove
        return result

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        await self._session.close()

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()
