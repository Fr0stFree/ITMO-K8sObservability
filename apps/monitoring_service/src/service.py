import asyncio
import logging
import logging.config
import signal

from monitoring_service.src.metric_server import MetricsServer
from monitoring_service.src.rpc_server import RPCServer
from monitoring_service.src.settings import MonitoringSettings


class MonitoringService:
    def __init__(self, settings: MonitoringSettings) -> None:
        self.settings = settings
        self.logger = self._new_logger()
        self.rpc_server = self._new_rpc_server()
        self.metrics_server = self._new_metrics_server()
        self.running = asyncio.Event()

    async def start(self):
        self.logger.info("Starting the app...")
        await self.rpc_server.start()
        self.metrics_server.start()
        self.logger.info("The app has been started")

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self.running.set)
        loop.add_signal_handler(signal.SIGTERM, self.running.set)

        await self.running.wait()
        await self.stop()

    async def stop(self):
        self.logger.info("Stopping the app...")
        await self.rpc_server.stop()
        self.metrics_server.stop()
        self.logger.info("The app has been stopped")

    def _new_logger(self) -> logging.Logger:
        logging.config.dictConfig(self.settings.logging)
        logger = logging.getLogger(self.__class__.__name__)
        return logger

    def _new_metrics_server(self) -> MetricsServer:
        metrics_server = MetricsServer(self.settings.metrics_server_port, self.logger)
        return metrics_server

    def _new_rpc_server(self) -> RPCServer:
        rpc_server = RPCServer(self.logger, self.settings.rpc_workers, self.settings.rpc_server_port)
        return rpc_server
