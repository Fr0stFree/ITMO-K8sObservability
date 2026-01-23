import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Protocol

from grpc.aio import Server, server

type IServicer = object


class IServicerRegisterer(Protocol):
    def __call__(self, servicer: IServicer, server: Server) -> None: ...


class GRPCServer:
    def __init__(
        self,
        servicer: IServicer,
        registerer: IServicerRegisterer,
        workers: int,
        port: int,
        logger: logging.Logger,
    ) -> None:
        self._registerer = registerer
        self._servicer = servicer
        self._workers = workers
        self._port = port
        self._logger = logger

        self._server: Server

    async def start(self) -> None:
        self._logger.info("Starting the rpc server on port %d...", self._port)
        self._server = server(ThreadPoolExecutor(max_workers=self._workers))
        self._registerer(self._servicer, self._server)
        self._server.add_insecure_port(f"[::]:{self._port}")

    async def stop(self) -> None:
        self._logger.info("Shutting down the rpc server...")
        await self._server.stop(1)

    async def is_healthy(self) -> bool:
        # TODO: need something more useful
        return True
