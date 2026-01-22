import asyncio
from concurrent import futures
import logging
import logging.config
import signal
from grpc.aio import server, Server

from monitoring_service.src.metrics import MetricsServer
from monitoring_service.src.rpc_servicer import RPCServicer
from monitoring_service.src.settings import MonitoringSettings

from protocol.monitoring_service_pb2_grpc import add_MonitoringServiceServicer_to_server


class MonitoringService:
    def __init__(self, settings: MonitoringSettings) -> None:
        self.settings = settings
        self.logger = self._new_logger()
        self.rpc_server = self._new_rpc_server()
        self.metrics_server = self._new_metrics_server()
        self.running = asyncio.Event()

    async def start(self):
        self.logger.info(f"Starting the app...")
        self.logger.info(f"Starting the rpc server on port {self.settings.rpc_server_port}...")
        await self.rpc_server.start()
        self.metrics_server.start()
        loop = asyncio.get_running_loop()
        for s in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(s, self.running.set)

    async def run(self):
        self.logger.info(f"The app has been started")
        await self.running.wait()
        await self.stop()

    async def stop(self):
        self.logger.info(f"Stopping the app...")
        await self.rpc_server.stop(1)
        self.metrics_server.stop()
        self.logger.info("The app has been stopped")

    def _new_rpc_server(self) -> Server:
        servicer = RPCServicer()
        workers, address = self.settings.rpc_workers, f"[::]:{self.settings.rpc_server_port}"
        rpc_server = server(futures.ThreadPoolExecutor(max_workers=workers))
        add_MonitoringServiceServicer_to_server(servicer, rpc_server)
        rpc_server.add_insecure_port(address)
        return rpc_server

    def _new_metrics_server(self):
        metrics_server = MetricsServer(self.settings.metrics_server_port, self.logger)
        return metrics_server

    def _new_logger(self) -> logging.Logger:
        logging.config.dictConfig(self.settings.logging)
        logger = logging.getLogger(self.__class__.__name__)
        return logger
