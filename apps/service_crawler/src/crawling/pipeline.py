import asyncio
from collections.abc import Sequence

from common.logs.logger import LoggerLike
from service_crawler.src.crawling.consumer import Consumer
from service_crawler.src.crawling.models import CrawledURL
from service_crawler.src.crawling.worker import Worker


async def callback(url: CrawledURL) -> None:
    print(f"CRAWLED NEW URL - {url.url}:{url.status}")


class CrawlingPipeline:
    def __init__(self, urls: Sequence[str], logger: LoggerLike, concurrent_workers: int) -> None:
        self._logger = logger
        self._queue = asyncio.Queue(maxsize=100)
        self._consumer = Consumer(self._queue, callback, logger)
        self._workers = [
            Worker(
                urls=list(urls[i : i + len(urls) // concurrent_workers]),
                logger=logger,
                results=self._queue,
            )
            for i in range(0, len(urls), len(urls) // concurrent_workers)
        ]

    async def start(self) -> None:
        self._logger.info("Starting crawling pipeline with %d workers..", len(self._workers))
        await self._consumer.start()
        for worker in self._workers:
            asyncio.create_task(worker.start())

    async def stop(self) -> None:
        self._logger.info("Stopping crawling pipeline...")
        await asyncio.gather(*(worker.stop() for worker in self._workers))
        await self._consumer.stop()

    async def is_healthy(self) -> bool:
        workers = await asyncio.gather(*(worker.is_healthy() for worker in self._workers))
        consumer = await self._consumer.is_healthy()
        return all(workers + [consumer])
