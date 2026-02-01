from grpc.aio import ServicerContext

from common.grpc.server import IServicerRegisterer
from protocol.analyzer_pb2 import GetTargetDetailsRequest, GetTargetDetailsResponse
from protocol.analyzer_pb2_grpc import AnalyzerServiceServicer, add_AnalyzerServiceServicer_to_server


class RPCServicer(AnalyzerServiceServicer):
    async def GetTargetDetails(
        self,
        request: GetTargetDetailsRequest,
        context: ServicerContext,
    ) -> GetTargetDetailsResponse:
        print(f"got request {request}")
        return GetTargetDetailsResponse(id="123", url="http://example.com", status="OK", checked_at=1625247600)

    @property
    def registerer(self) -> IServicerRegisterer:
        return add_AnalyzerServiceServicer_to_server
