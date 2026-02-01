import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service_crawler.src.crawling.crawling import CrawlingPipeline


def new_crawling_pipeline(concurrent_workers: int) -> "CrawlingPipeline":
    from service_crawler.src.crawling.crawling import CrawlingPipeline, Worker

    queue = asyncio.Queue(maxsize=100)
    workers = [Worker(queue) for _ in range(concurrent_workers)]
    return CrawlingPipeline(queue, workers)
