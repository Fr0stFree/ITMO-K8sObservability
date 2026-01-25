import asyncio
import datetime as dt
from http import HTTPMethod
import signal

from dependency_injector.wiring import Provide, inject

from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from common.tracing import TraceExporter
from common.utils.health import check_health
from service_crawler.src import http
from service_crawler.src.container import Container
from service_crawler.src.crawling import CrawlingPipeline


class CrawlerService:

    @inject
    def __init__(self, http_server: HTTPServer = Provide[Container.http_server]) -> None:
        http_server.add_handler(
            path="/health", handler=lambda request: http.health(request, self.is_healthy), method=HTTPMethod.GET
        )

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
        trace_exporter: TraceExporter = Provide[Container.trace_exporter],
        pipeline: CrawlingPipeline = Provide[Container.crawling_pipeline],
    ) -> None:
        logger.info("Starting the app...")
        running = asyncio.Event()
        for component in (grpc_server, metrics_server, http_server, trace_exporter, pipeline):
            await component.start()
        logger.info("The app has been started")

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, running.set)
        loop.add_signal_handler(signal.SIGTERM, running.set)

        await running.wait()
        await self.stop()

    @inject
    async def is_healthy(
        self,
        health_check_timeout: dt.timedelta = Provide[Container.settings.health_check_timeout],
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
        trace_exporter: TraceExporter = Provide[Container.trace_exporter],
        pipeline: CrawlingPipeline = Provide[Container.crawling_pipeline],
    ) -> bool:
        result = await check_health(
            http_server,
            metrics_server,
            grpc_server,
            trace_exporter,
            pipeline,
            timeout=health_check_timeout,
        )
        logger.info(
            "Health check result: %s",
            ", ".join(f"{comp.__class__.__name__}: {status}" for comp, status in result.items()),
        )
        return all(result.values())

    @inject
    async def stop(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_server: GRPCServer = Provide[Container.grpc_server],
        trace_exporter: TraceExporter = Provide[Container.trace_exporter],
        pipeline: CrawlingPipeline = Provide[Container.crawling_pipeline],
    ) -> None:
        logger.info("Stopping the app...")
        for component in (grpc_server, metrics_server, http_server, trace_exporter, pipeline):
            try:
                await component.stop()
            except Exception as error:
                logger.warning(
                    "An error occurred while stopping the %s: %s",
                    component.__class__.__name__,
                    error,
                )

        logger.info("The app has been stopped")
