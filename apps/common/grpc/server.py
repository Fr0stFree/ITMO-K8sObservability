from concurrent.futures import ThreadPoolExecutor

from grpc.aio import Server, server, ServerInterceptor

from common.grpc.interface import IServicer, IServicerRegisterer
from common.grpc.settings import GRPCServerSettings
from common.logs import LoggerLike


class GRPCServer:
    def __init__(
        self,
        servicer: IServicer,
        settings: GRPCServerSettings,
        registerer: IServicerRegisterer,
        logger: LoggerLike,
    ) -> None:
        self._registerer = registerer
        self._servicer = servicer
        self._settings = settings
        self._logger = logger
        self._server: Server
        self._interceptors: list[ServerInterceptor] = []

    def add_interceptor(self, interceptor: ServerInterceptor) -> None:
        self._interceptors.append(interceptor)

    async def start(self) -> None:
        self._logger.info("Starting the grpc server on port %d...", self._settings.port)
        self._server = server(
            ThreadPoolExecutor(max_workers=self._settings.workers_amount),
            interceptors=self._interceptors,
        )
        self._registerer(self._servicer, self._server)
        self._server.add_insecure_port(f"[::]:{self._settings.port}")
        await self._server.start()

    async def stop(self) -> None:
        self._logger.info("Shutting down the grpc server...")
        await self._server.stop(1)

    async def is_healthy(self) -> bool:
        # TODO: need something more useful
        return True
