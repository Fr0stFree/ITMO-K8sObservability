import asyncio
import signal
from http import HTTPMethod

from dependency_injector.wiring import Provide, inject

from common.grpc.server import GRPCServer
from common.http.server import HTTPServer
from common.logs.logger import LoggerLike
from common.metrics.server import MetricsServer
from monitoring_service.src import http
from monitoring_service.src.container import Container


class MonitoringService:

    @inject
    def __init__(self, http_server: HTTPServer = Provide[Container.http_server]) -> None:
        self._running = asyncio.Event()

        # setup handlers
        http_server.add_handler(path="/health", handler=http.health, method=HTTPMethod.GET)

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
    ) -> None:
        logger.info("Starting the app...")
        await grpc_server.start()
        await metrics_server.start()
        await http_server.start()
        logger.info("The app has been started")

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self._running.set)
        loop.add_signal_handler(signal.SIGTERM, self._running.set)

        await self._running.wait()
        await self.stop()

    @inject
    async def stop(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
    ) -> None:
        logger.info("Stopping the app...")
        await grpc_server.stop()
        await metrics_server.stop()
        await http_server.stop()
        logger.info("The app has been stopped")
