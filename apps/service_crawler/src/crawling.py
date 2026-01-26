import asyncio
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import asdict, dataclass
import datetime as dt
from hashlib import md5
from itertools import cycle
from typing import Final, Literal

from aiohttp import ClientSession, ClientTimeout
from redis.asyncio import Redis

from common.brokers.interface import IBrokerProducer
from common.logs import LoggerLike


@dataclass
class CrawledURL:
    url: str
    status: Literal["UP", "DOWN"]
    updated_at: str


class CrawlingPipeline:
    def __init__(
        self,
        logger: LoggerLike,
        concurrent_workers: int,
        producer: IBrokerProducer,
        redis: Redis,
    ) -> None:
        self._logger = logger
        self._producer = producer
        self._redis = redis
        self._workers_amount = concurrent_workers
        self._queue = asyncio.Queue(maxsize=100)
        self._processor: asyncio.Task | None = None
        self._workers = [Worker(logger=self._logger, queue=self._queue) for _ in range(self._workers_amount)]

    async def _process_urls(self) -> None:
        while True:
            crawled_url = await self._queue.get()
            await self._producer.send(asdict(crawled_url))
            self._queue.task_done()

    async def start(self) -> None:
        urls = await self._redis.smembers("crawling_urls")
        self._logger.info("Fetched %d URL(s) to crawl from Redis", len(urls))
        if not urls:
            raise RuntimeError("No URLs to crawl found in Redis")

        for url in urls:
            worker_index = int(md5(url.encode(), usedforsecurity=False).hexdigest(), 16) % self._workers_amount
            self._workers[worker_index].add_urls([url])

        self._logger.info("Starting crawling pipeline with %d worker(s)...", len(self._workers))
        self._processor = asyncio.create_task(self._process_urls())
        for worker in self._workers:
            await worker.start()

    async def stop(self) -> None:
        self._logger.info("Stopping crawling pipeline...")
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

    def __init__(self, logger: LoggerLike, queue: asyncio.Queue[CrawledURL]) -> None:
        self._urls_to_crawl = set()
        self._queue = queue
        self._logger = logger
        self._session = ClientSession()  # TODO: upgrade
        self._task: asyncio.Task | None = None

    def add_urls(self, urls: Iterable[str]) -> None:
        self._urls_to_crawl.update(urls)

    def remove_urls(self, urls: Iterable[str]) -> None:
        self._urls_to_crawl.difference_update(urls)

    async def start(self) -> None:
        asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            for url in cycle(self._urls_to_crawl):
                crawled_url = await self._crawl(url)
                await self._queue.put(crawled_url)

    async def _crawl(self, url: str) -> CrawledURL:
        try:
            async with self._session.get(url, timeout=self.REQUEST_TIMEOUT) as response:
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
