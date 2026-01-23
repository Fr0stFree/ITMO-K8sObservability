import logging
from threading import Thread
from wsgiref.simple_server import WSGIServer

from prometheus_client import start_http_server


class MetricsServer:
    def __init__(self, port: int, logger: logging.Logger) -> None:
        self.port = port
        self.logger = logger

        self.server: WSGIServer
        self.thread: Thread

    async def start(self) -> None:
        self.logger.info("Starting the metrics server on port %d...", self.port)
        self.server, self.thread = start_http_server(self.port)

    async def stop(self) -> None:
        self.logger.info("Shutting down the metrics server...")
        self.server.shutdown()

    async def is_healthy(self) -> bool:
        return self.thread.is_alive()
