import logging
from threading import Thread
from wsgiref.simple_server import WSGIServer
from prometheus_client import Counter, Histogram, start_http_server


class MetricsServer:
    def __init__(self, port: int, logger: logging.Logger) -> None:
        self.port = port
        self.logger = logger
        self.server: WSGIServer
        self.thread: Thread

    def start(self):
        self.logger.info(f"Starting the metrics server on port {self.port}...")
        self.server, self.thread = start_http_server(self.port)

    def stop(self):
        self.logger.info("Shutting down the metrics server...")
        self.server.shutdown()


RPC_CALLS_TOTAL = Counter("rpc_calls_total", "Total number of gRPC calls", ["method", "status"])

RPC_LATENCY_SECONDS = Histogram("rpc_latency_seconds", "Latency of gRPC calls in seconds", ["method"])
