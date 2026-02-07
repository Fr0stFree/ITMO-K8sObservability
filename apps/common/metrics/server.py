from threading import Thread
from wsgiref.simple_server import WSGIServer

from prometheus_client import start_http_server

from common.logs import LoggerLike


class MetricsServer:
    def __init__(self, port: int, logger: LoggerLike) -> None:
        self._port = port
        self._logger = logger

        self._server: WSGIServer
        self._thread: Thread

    async def start(self) -> None:
        self._logger.info("Starting the metrics server on port %d...", self._port)
        self._server, self._thread = start_http_server(self._port)

    async def stop(self) -> None:
        self._logger.info("Shutting down the metrics server...")
        self._server.shutdown()

    async def is_healthy(self) -> bool:
        return self._thread.is_alive()
