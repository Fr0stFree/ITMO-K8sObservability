import asyncio
import signal
from http import HTTPMethod
from typing import Callable

from common.grpc.server import GRPCServer
from common.http.health import HealthHandler
from common.http.server import HTTPServer
from common.logs.logger import LoggerLike, new_logger
from common.metrics.server import MetricsServer
from monitoring_service.src.rpc import RPCServicer
from monitoring_service.src.settings import MonitoringSettings


class MonitoringService:
    def __init__(
        self,
        settings: MonitoringSettings,
        logger_factory: Callable[..., LoggerLike] = new_logger,
        rpc_servicer_factory: Callable[..., RPCServicer] = RPCServicer,
        grpc_server_factory: Callable[..., GRPCServer] = GRPCServer,
        http_server_factory: Callable[..., HTTPServer] = HTTPServer,
        metrics_server_factory: Callable[..., MetricsServer] = MetricsServer,
    ) -> None:
        self._settings = settings
        self._logger = logger_factory(config=settings.logging, name=self.__class__.__name__)
        rpc_servicer = rpc_servicer_factory()
        self._grpc_server = grpc_server_factory(
            servicer=rpc_servicer,
            registerer=rpc_servicer.registerer,
            workers=settings.grpc_workers,
            port=settings.grpc_server_port,
            logger=self._logger,
        )
        self._http_server = http_server_factory(port=settings.http_server_port, logger=self._logger)
        self._metrics_server = metrics_server_factory(port=settings.metrics_server_port, logger=self._logger)
        self._running = asyncio.Event()

        health_handler = HealthHandler(self._http_server, self._metrics_server, self._grpc_server, logger=self._logger)
        self._http_server.add_handler(path="/health", handler=health_handler, method=HTTPMethod.GET)

    async def start(self):
        self._logger.info("Starting the app...")
        await self._grpc_server.start()
        await self._metrics_server.start()
        await self._http_server.start()
        self._logger.info("The app has been started")

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._running.set)
        loop.add_signal_handler(signal.SIGTERM, self._running.set)

        await self._running.wait()
        await self.stop()

    async def stop(self):
        self._logger.info("Stopping the app...")
        await self._grpc_server.stop()
        await self._metrics_server.stop()
        await self._http_server.stop()
        self._logger.info("The app has been stopped")
