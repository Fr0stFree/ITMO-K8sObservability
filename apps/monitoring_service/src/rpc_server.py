import logging
from concurrent.futures import ThreadPoolExecutor

from google.protobuf.empty_pb2 import Empty
from grpc.aio import Server, ServicerContext, server

from protocol.monitoring_service_pb2 import AddTargetRequest
from protocol.monitoring_service_pb2_grpc import MonitoringServiceServicer, add_MonitoringServiceServicer_to_server


class RPCServicer(MonitoringServiceServicer):

    async def AddTarget(
        self,
        request: AddTargetRequest,
        context: ServicerContext,
    ) -> Empty:
        print(f"got request {request}")
        return Empty()


class RPCServer:
    def __init__(self, logger: logging.Logger, workers: int, port: int) -> None:
        self._servicer = RPCServicer()
        self._workers = workers
        self._port = port
        self._logger = logger
        self._server: Server

    async def start(self) -> None:
        self._logger.info("Starting the rpc server on port %d...", self._port)
        self._server = server(ThreadPoolExecutor(max_workers=self._workers))
        add_MonitoringServiceServicer_to_server(self._servicer, self._server)
        self._server.add_insecure_port(f"[::]:{self._port}")

    async def stop(self) -> None:
        self._logger.info("Shutting down the rpc server...")
        await self._server.stop(1)
