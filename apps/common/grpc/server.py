from concurrent.futures import ThreadPoolExecutor

from common.grpc.interface import IRPCServicer
from common.grpc.settings import GRPCServerSettings
from common.logs import LoggerLike
from grpc.aio import Server, ServerInterceptor, server


class GRPCServer:
    def __init__(
        self,
        settings: GRPCServerSettings,
        logger: LoggerLike,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._interceptors: list[ServerInterceptor] = []
        self._server: Server
        self._servicer: IRPCServicer

    def setup_servicer(self, servicer: IRPCServicer) -> None:
        self._servicer = servicer

    def add_interceptor(self, interceptor: ServerInterceptor) -> None:
        self._interceptors.append(interceptor)

    async def start(self) -> None:
        self._logger.info("Starting the grpc server on port %d...", self._settings.port)
        self._server = server(
            ThreadPoolExecutor(max_workers=self._settings.workers_amount),
            interceptors=self._interceptors,
        )
        self._servicer.add_to_server(self._server)
        self._server.add_insecure_port(f"[::]:{self._settings.port}")
        await self._server.start()

    async def stop(self) -> None:
        self._logger.info("Shutting down the grpc server...")
        await self._server.stop(1)

    async def is_healthy(self) -> bool:
        # TODO: need something more useful
        return True
