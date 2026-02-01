import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service_analyzer.src.grpc.servicer import RPCServicer
    from service_crawler.src.crawling.pipeline import CrawlingPipeline


def new_crawling_pipeline(concurrent_workers: int) -> "CrawlingPipeline":
    from service_crawler.src.crawling.pipeline import CrawlingPipeline, Worker

    queue = asyncio.Queue(maxsize=100)
    workers = [Worker(queue, idx) for idx in range(concurrent_workers)]
    return CrawlingPipeline(queue, workers)


def new_rpc_servicer() -> "RPCServicer":
    from service_crawler.src.grpc.servicer import RPCServicer

    return RPCServicer()
