from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext

from common.grpc.server import IServicerRegisterer
from protocol.monitoring_service_pb2 import AddTargetRequest
from protocol.monitoring_service_pb2_grpc import (
    MonitoringServiceServicer,
    add_MonitoringServiceServicer_to_server,
)


class RPCServicer(MonitoringServiceServicer):

    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
    ) -> Empty:
        print(f"got request {request}")
        return Empty()

    @property
    def registerer(self) -> IServicerRegisterer:
        return add_MonitoringServiceServicer_to_server
