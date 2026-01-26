import asyncio
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import asdict
import json

from common.brokers.interface import IBrokerProducer
from common.logs import LoggerLike
from service_crawler.src.crawling.worker import Worker


class CrawlingPipeline:
    def __init__(
        self,
        urls: Sequence[str],
        logger: LoggerLike,
        concurrent_workers: int,
        producer: IBrokerProducer,
    ) -> None:
        self._logger = logger
        self._queue = asyncio.Queue(maxsize=100)
        self._processor: asyncio.Task | None = None
        self._producer = producer
        self._workers = [
            Worker(
                urls=list(urls[i : i + len(urls) // concurrent_workers]),
                logger=logger,
                queue=self._queue,
            )
            for i in range(0, len(urls), len(urls) // concurrent_workers)
        ]

    async def _process_urls(self) -> None:
        while True:
            crawled_url = await self._queue.get()
            message = json.dumps(asdict(crawled_url)).encode("utf-8")
            await self._producer.send(message)
            self._queue.task_done()

    async def start(self) -> None:
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
