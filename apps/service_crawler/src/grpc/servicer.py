from dependency_injector.wiring import Provide, inject
from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext
from opentelemetry.trace import Span
from grpc.aio import Server
from common.databases.redis.client import RedisClient

from protocol.crawler_pb2 import AddTargetRequest, RemoveTargetRequest
from protocol.crawler_pb2_grpc import (
    CrawlerServiceServicer,
    add_CrawlerServiceServicer_to_server,
)

from service_crawler.src.container import Container
from service_crawler.src.crawling.pipeline import CrawlingPipeline


class RPCServicer(CrawlerServiceServicer):

    @inject
    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
        span: Span = Provide[Container.current_span],
        db_client: RedisClient = Provide[Container.db_client],
        pipeline: CrawlingPipeline = Provide[Container.crawling_pipeline],
    ) -> Empty:
        await db_client.redis.sadd("crawling_urls", request.target_url)
        pipeline.register_urls([request.target_url])
        span.set_attribute("target.url", request.target_url)
        return Empty()

    @inject
    async def RemoveTarget(
        self,
        request: RemoveTargetRequest,
        context: ServicerContext,
        span: Span = Provide[Container.current_span],
        db_client: RedisClient = Provide[Container.db_client],
        pipeline: CrawlingPipeline = Provide[Container.crawling_pipeline],
    ) -> Empty:
        await db_client.redis.srem("crawling_urls", request.target_url)
        pipeline.unregister_urls([request.target_url])
        span.set_attribute("target.url", request.target_url)
        return Empty()

    def add_to_server(self, server: Server) -> None:
        return add_CrawlerServiceServicer_to_server(self, server)
