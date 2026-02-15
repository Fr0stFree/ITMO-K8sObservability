from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from service_analyzer.src.grpc.servicer import RPCServicer
    from service_crawler.src.crawling.worker_manager import CrawlingWorkerManager
    from service_crawler.src.db.repo import Repository


def new_worker_manager(concurrent_workers: int) -> "CrawlingWorkerManager":
    from service_crawler.src.crawling.worker_manager import CrawlingWorkerManager, Worker

    workers = [Worker(idx) for idx in range(concurrent_workers)]
    return CrawlingWorkerManager(workers)


def new_rpc_servicer() -> "RPCServicer":
    from service_crawler.src.grpc.servicer import RPCServicer

    return RPCServicer()


def new_repository() -> "Repository":
    from service_crawler.src.db.repo import Repository

    return Repository()
