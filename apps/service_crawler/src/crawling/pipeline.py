import asyncio
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import asdict
from hashlib import md5

from dependency_injector.wiring import Provide, inject
from opentelemetry.propagate import extract as extract_context
from opentelemetry.trace import Tracer

from common.brokers.interface import IBrokerProducer
from common.databases.redis.client import RedisClient
from common.logs import LoggerLike
from service_crawler.src.container import Container
from service_crawler.src.crawling.worker import Worker


class CrawlingPipeline:
    def __init__(
        self,
        queue: asyncio.Queue,
        workers: Sequence[Worker],
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
