from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext

from common.grpc.server import IServicerRegisterer
from protocol.crawler_pb2 import AddTargetRequest
from protocol.crawler_pb2_grpc import (
    CrawlerServiceServicer,
    add_CrawlerServiceServicer_to_server,
)


class RPCServicer(CrawlerServiceServicer):
    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
    ) -> Empty:
        print(f"got request {request}")
        return Empty()

    @property
    def registerer(self) -> IServicerRegisterer:
        return add_CrawlerServiceServicer_to_server
