from dependency_injector.wiring import Provide, inject
from google.protobuf.empty_pb2 import Empty
from grpc.aio import Server, ServicerContext
from opentelemetry.trace import Span

from protocol.crawler_pb2 import AddTargetRequest, RemoveTargetRequest
from protocol.crawler_pb2_grpc import (
    CrawlerServiceServicer,
    add_CrawlerServiceServicer_to_server,
)
from service_crawler.src.container import Container
from service_crawler.src.crawling.worker_manager import CrawlingWorkerManager
from service_crawler.src.db.repo import Repository


class RPCServicer(CrawlerServiceServicer):

    @inject
    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
        span: Span = Provide[Container.current_span],
        repo: Repository = Provide[Container.repository],
        manager: CrawlingWorkerManager = Provide[Container.worker_manager],
    ) -> Empty:
        await repo.add_target(request.target_url)
        manager.register_urls([request.target_url])
        span.set_attribute("target.url", request.target_url)
        return Empty()

    @inject
    async def RemoveTarget(
        self,
        request: RemoveTargetRequest,
        context: ServicerContext,
        span: Span = Provide[Container.current_span],
        repo: Repository = Provide[Container.repository],
        manager: CrawlingWorkerManager = Provide[Container.worker_manager],
    ) -> Empty:
        await repo.remove_target(request.target_url)
        manager.unregister_urls([request.target_url])
        span.set_attribute("target.url", request.target_url)
        return Empty()

    def add_to_server(self, server: Server) -> None:
        return add_CrawlerServiceServicer_to_server(self, server)
