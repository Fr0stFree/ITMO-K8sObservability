import asyncio
import datetime as dt
from collections.abc import Iterable
from contextlib import suppress
from http import HTTPMethod
from itertools import cycle

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
        timeout: dt.timedelta = Provide[Container.settings.worker_request_timeout],
    ) -> None:
        self._queue = queue
        self._urls_to_crawl = set()
        self._session = ClientSession()  # TODO: upgrade
        self._task: asyncio.Task | None = None
        self._timeout = ClientTimeout(total=timeout.total_seconds())

    def add_urls(self, urls: Iterable[str]) -> None:
        self._urls_to_crawl.update(urls)

    def remove_urls(self, urls: Iterable[str]) -> None:
        self._urls_to_crawl.difference_update(urls)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    @inject
    async def _run(
        self,
        tracer: Tracer = Provide[Container.tracer],
        counter: Counter = Provide[Container.crawled_urls_counter],
    ) -> None:
        while True:
            for url in cycle(self._urls_to_crawl):
                with tracer.start_as_current_span(
                    "http.crawl",
                    attributes={"http.url": url, "http.method": HTTPMethod.GET},
                ):
                    url = await self._crawl(url)
                    counter.labels(status=url.status).inc()
                    meta = {}
                    inject_context(meta)
                    await self._queue.put((url, meta))

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
            # span.record_exception(error)
            span.set_status(StatusCode.ERROR)

        await asyncio.sleep(1)  # TODO: remove
        return result

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        await self._session.close()

    async def is_healthy(self) -> bool:
        return self._task is not None and not self._task.done()
