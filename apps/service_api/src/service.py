import asyncio
from http import HTTPMethod
import signal

from dependency_injector.wiring import Provide, inject

from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from common.tracing import TraceExporter
from service_api.src import http
from service_api.src.container import Container


class APIService:

    @inject
    def __init__(self, http_server: HTTPServer = Provide[Container.http_server]) -> None:
        http_server.add_handler(path="/health", handler=http.health, method=HTTPMethod.GET)
        http_server.add_handler(path="/create_target", handler=http.create_target, method=HTTPMethod.GET)

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: HTTPServer = Provide[Container.http_server],
        metrics_server: MetricsServer = Provide[Container.metrics_server],
        grpc_client: GRPCClient = Provide[Container.grpc_client],
        trace_exporter: TraceExporter = Provide[Container.trace_exporter],
    ) -> None:
        logger.info("Starting the app...")
        running = asyncio.Event()
        for component in (grpc_client, metrics_server, http_server, trace_exporter):
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
        grpc_client: GRPCClient = Provide[Container.grpc_client],
        trace_exporter: TraceExporter = Provide[Container.trace_exporter],
    ) -> None:
        logger.info("Stopping the app...")
        for component in (grpc_client, metrics_server, http_server, trace_exporter):
            try:
                await component.stop()
            except Exception as error:
                logger.warning(
                    "An error occurred while stopping the %s: %s",
                    component.__class__.__name__,
                    error,
                )

        logger.info("The app has been stopped")


# @asynccontextmanager
# async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
#     logger.info("Starting the application...")
#     channel = grpc.aio.insecure_channel("localhost:50051")
#     crawler_service = CrawlerServiceStub(channel)
#     app.state.crawler_service = crawler_service

#     yield

#     await channel.close()
#     logger.info("Application shutdown...")


# @app.get("/{url}")
# async def root(url: str) -> str:
#     app.state.crawler_service.AddTarget(AddTargetRequest(target_url=url))
#     return "OK"
