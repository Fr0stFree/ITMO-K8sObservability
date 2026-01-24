import asyncio
from collections.abc import Sequence

from common.logs.logger import LoggerLike
from service_crawler.src.crawling.consumer import Consumer
from service_crawler.src.crawling.models import CrawledURL
from service_crawler.src.crawling.worker import WorkerPool


async def callback(url: CrawledURL) -> None:
    print(f"CRAWLED NEW URL - {url.url}:{url.status}")


class CrawlingPipeline:
    def __init__(self, urls: Sequence[str], logger: LoggerLike, concurrent_workers: int) -> None:
        self._logger = logger
        self._queue = asyncio.Queue(maxsize=100)
        self._pool = WorkerPool(amount=concurrent_workers, urls=urls, queue=self._queue, logger=logger)
        self._consumer = Consumer(self._queue, callback, logger)

    async def start(self) -> None:
        self._logger.info("Starting crawling pipeline with %d workers..", self._pool.amount)
        await self._consumer.start()
        await self._pool.start()

    async def stop(self) -> None:
        self._logger.info("Stopping crawling pipeline...")
        await self._pool.stop()
        await self._consumer.stop()

    async def is_healthy(self) -> bool:
        tasks = [self._pool.is_healthy(), self._consumer.is_healthy()]
        result = await asyncio.gather(*tasks)
        return all(result)
