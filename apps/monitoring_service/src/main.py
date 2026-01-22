from concurrent import futures
from grpc import ServicerContext, server

from google.protobuf.empty_pb2 import Empty

from protocol.monitoring_service_pb2_grpc import MonitoringServiceServicer, add_MonitoringServiceServicer_to_server
from protocol.monitoring_service_pb2 import AddTargetRequest


class GreeterService(MonitoringServiceServicer):

    def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
    ) -> Empty:
        print(f"got request {request}")
        return Empty()


def serve() -> None:
    service = server(futures.ThreadPoolExecutor(max_workers=10))
    add_MonitoringServiceServicer_to_server(
        GreeterService(),
        service,
    )
    service.add_insecure_port("[::]:50051")
    service.start()
    service.wait_for_termination()


if __name__ == "__main__":
    serve()
