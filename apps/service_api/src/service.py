import asyncio
import datetime as dt
from http import HTTPMethod
import signal

from dependency_injector.wiring import Provide, inject

from common.http import IHTTPServer
from common.logs import LoggerLike
from common.types.interface import IHealthCheck, ILifeCycle
from common.utils.health import check_health
from service_api.src.container import Container
from service_api.src.http import handlers, middleware


class APIService:

    @inject
    def __init__(self, http_server: IHTTPServer = Provide[Container.http_server]) -> None:
        http_server.add_middleware(middleware.observability)
        http_server.add_handler(
            path="/health", handler=lambda request: handlers.health(request, self.is_healthy), method=HTTPMethod.GET
        )
        http_server.add_handler(path="/targets", handler=handlers.add_target, method=HTTPMethod.POST)
        http_server.add_handler(path="/targets/{target_id}", handler=handlers.get_target, method=HTTPMethod.GET)
        http_server.add_handler(path="/targets", handler=handlers.list_targets, method=HTTPMethod.GET)
        http_server.add_handler(path="/targets/{target_id}", handler=handlers.delete_target, method=HTTPMethod.DELETE)

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: ILifeCycle = Provide[Container.http_server],
        metrics_server: ILifeCycle = Provide[Container.metrics_server],
        trace_exporter: ILifeCycle = Provide[Container.trace_exporter],
        crawler_client: ILifeCycle = Provide[Container.crawler_client],
        analyzer_client: ILifeCycle = Provide[Container.analyzer_client],
    ) -> None:
        logger.info("Starting the app...")
        running = asyncio.Event()
        for component in (crawler_client, analyzer_client, metrics_server, http_server, trace_exporter):
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
        http_server: IHealthCheck = Provide[Container.http_server],
        metrics_server: IHealthCheck = Provide[Container.metrics_server],
        trace_exporter: IHealthCheck = Provide[Container.trace_exporter],
        crawler_client: IHealthCheck = Provide[Container.crawler_client],
        analyzer_client: IHealthCheck = Provide[Container.analyzer_client],
    ) -> bool:
        result = await check_health(
            http_server,
            metrics_server,
            trace_exporter,
            crawler_client,
            analyzer_client,
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
        http_server: ILifeCycle = Provide[Container.http_server],
        metrics_server: ILifeCycle = Provide[Container.metrics_server],
        trace_exporter: ILifeCycle = Provide[Container.trace_exporter],
        crawler_client: ILifeCycle = Provide[Container.crawler_client],
        analyzer_client: ILifeCycle = Provide[Container.analyzer_client],
    ) -> None:
        logger.info("Stopping the app...")
        for component in (crawler_client, analyzer_client, metrics_server, http_server, trace_exporter):
            try:
                await component.stop()
            except Exception as error:
                logger.warning("An error occurred while stopping the %s: %s", component.__class__.__name__, error)

        logger.info("The app has been stopped")
