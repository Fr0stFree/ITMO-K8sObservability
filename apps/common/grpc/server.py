from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from grpc.aio import Server, server

from common.grpc.settings import GRPCServerSettings
from common.logs.logger import LoggerLike

type IServicer = object


class IServicerRegisterer(Protocol):
    def __call__(self, servicer: IServicer, server: Server) -> None: ...


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

    async def start(self) -> None:
        self._logger.info("Starting the grpc server on port %d...", self._settings.port)
        self._server = server(ThreadPoolExecutor(max_workers=self._settings.workers_amount))
        self._registerer(self._servicer, self._server)
        self._server.add_insecure_port(f"[::]:{self._settings.port}")

    async def stop(self) -> None:
        self._logger.info("Shutting down the grpc server...")
        await self._server.stop(1)

    async def is_healthy(self) -> bool:
        # TODO: need something more useful
        return True
