import asyncio
from collections.abc import Iterable, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
import datetime as dt
from enum import StrEnum
from hashlib import md5
from http import HTTPMethod
from itertools import cycle
from typing import Final

from aiohttp import ClientSession, ClientTimeout
from dependency_injector.wiring import Provide, inject
from opentelemetry.propagate import extract as extract_context, inject as inject_context
from opentelemetry.trace import Tracer
from opentelemetry.trace.span import Span
from opentelemetry.trace.status import StatusCode
from prometheus_client import Counter

from common.brokers.interface import IBrokerProducer
from common.databases.redis.client import RedisClient
from common.logs import LoggerLike
from service_crawler.src.container import Container


class ResourceStatus(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


@dataclass
class CrawledURL:
    url: str
    status: ResourceStatus
    updated_at: str
    comment: str | None = None


class CrawlingPipeline:
    def __init__(
        self,
        queue: asyncio.Queue,
        workers: Sequence["Worker"],
    ) -> None:
        self._workers = workers
        self._queue = queue
        self._processor: asyncio.Task | None = None

    @inject
    async def _process_urls(
        self,
        producer: IBrokerProducer = Provide[Container.broker_producer],
        tracer: Tracer = Provide[Container.tracer],
    ) -> None:
        while True:
            payload, meta = await self._queue.get()
            with tracer.start_as_current_span("broker.produce", context=extract_context(meta)):
                try:
                    await producer.send(asdict(payload), meta)
                finally:
                    self._queue.task_done()

    @inject
    async def start(
        self,
        db: RedisClient = Provide[Container.db_client],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        urls = await db.redis.smembers("crawling_urls")
        logger.info("Fetched %d URL(s) to crawl from Redis", len(urls))
        if not urls:
            raise RuntimeError("No URLs to crawl found in Redis")

        for url in urls:
            worker_index = int(md5(url.encode(), usedforsecurity=False).hexdigest(), 16) % len(self._workers)
            self._workers[worker_index].add_urls([url])

        logger.info("Starting crawling pipeline with %d worker(s)...", len(self._workers))
        self._processor = asyncio.create_task(self._process_urls())
        for worker in self._workers:
            await worker.start()

    @inject
    async def stop(self, logger: LoggerLike = Provide[Container.logger]) -> None:
        logger.info("Stopping crawling pipeline...")
        await asyncio.gather(*(worker.stop() for worker in self._workers))
        if not self._processor:
            return

        self._processor.cancel()
        with suppress(asyncio.CancelledError):
            await self._processor
        self._processor = None

    async def is_healthy(self) -> bool:
        workers = await asyncio.gather(*(worker.is_healthy() for worker in self._workers))
        processor = self._processor is not None and not self._processor.done()
        return all(workers + [processor])


class Worker:
    REQUEST_TIMEOUT: Final[ClientTimeout] = ClientTimeout(total=10)

    def __init__(self, queue: asyncio.Queue) -> None:
        self._queue = queue
        self._urls_to_crawl = set()
        self._session = ClientSession()  # TODO: upgrade
        self._task: asyncio.Task | None = None

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
            async with self._session.get(url, timeout=self.REQUEST_TIMEOUT) as response:
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
