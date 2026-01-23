import asyncio
import signal
from http import HTTPMethod

from dependency_injector.wiring import Provide, inject

from common.databases.postgres.client import PostgresClient
from common.grpc.server import GRPCServer
from common.http.server import HTTPServer
from common.logs.logger import LoggerLike
from common.metrics.server import MetricsServer
from monitoring_service.src.container import Container
from monitoring_service.src.handlers import http


class MonitoringService:

    @inject
    def __init__(self, http_server: HTTPServer = Provide[Container.http_server]) -> None:
        http_server.add_handler(path="/health", handler=http.health, method=HTTPMethod.GET)

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
        db_client: PostgresClient = Provide[Container.db_client],
    ) -> None:
        logger.info("Starting the app...")
        running = asyncio.Event()
        for component in (grpc_server, metrics_server, http_server, db_client):
            await component.start()
        logger.info("The app has been started")

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, running.set)
        loop.add_signal_handler(signal.SIGTERM, running.set)

        await running.wait()
        await self.stop()

    @inject
    async def stop(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
        db_client: PostgresClient = Provide[Container.db_client],
    ) -> None:
        logger.info("Stopping the app...")
        for component in (grpc_server, metrics_server, http_server, db_client):
            try:
                await component.stop()
            except Exception as error:
                logger.warning("An error occurred while stopping the %s: %s", component.__class__.__name__, error)

        logger.info("The app has been stopped")
