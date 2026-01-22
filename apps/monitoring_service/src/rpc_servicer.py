from google.protobuf.empty_pb2 import Empty
from grpc.aio import ServicerContext
from protocol.monitoring_service_pb2_grpc import MonitoringServiceServicer
from protocol.monitoring_service_pb2 import AddTargetRequest


class RPCServicer(MonitoringServiceServicer):

    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
    ) -> Empty:
        print(f"got request {request}")
        return Empty()
