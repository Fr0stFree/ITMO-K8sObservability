import asyncio
import datetime as dt
from http import HTTPMethod
import signal

from dependency_injector.wiring import Provide, inject

from common.brokers.interface import IBrokerConsumer
from common.http import IHTTPServer
from common.logs import LoggerLike
from common.types.interface import IHealthCheck, ILifeCycle
from common.utils.health import check_health
from service_analyzer.src import broker, http
from service_analyzer.src.container import Container


class AnalyzerService:

    @inject
    def __init__(
        self,
        http_server: IHTTPServer = Provide[Container.http_server],
        broker_consumer: IBrokerConsumer = Provide[Container.broker_consumer],
    ) -> None:
        http_server.add_handler(
            path="/health", handler=lambda request: http.health(request, self.is_healthy), method=HTTPMethod.GET
        )
        broker_consumer.set_message_handler(broker.on_new_message)

    @inject
    async def start(
        self,
        logger: LoggerLike = Provide[Container.logger],
        http_server: ILifeCycle = Provide[Container.http_server],
        metrics_server: ILifeCycle = Provide[Container.metrics_server],
        grpc_server: ILifeCycle = Provide[Container.grpc_server],
        trace_exporter: ILifeCycle = Provide[Container.trace_exporter],
        db_client: ILifeCycle = Provide[Container.db_client],
        broker_consumer: ILifeCycle = Provide[Container.broker_consumer],
    ) -> None:
        logger.info("Starting the app...")
        running = asyncio.Event()
        for component in (grpc_server, db_client, metrics_server, http_server, trace_exporter, broker_consumer):
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
        grpc_server: IHealthCheck = Provide[Container.grpc_server],
        trace_exporter: IHealthCheck = Provide[Container.trace_exporter],
        db_client: IHealthCheck = Provide[Container.db_client],
        broker_consumer: IHealthCheck = Provide[Container.broker_consumer],
    ) -> bool:
        result = await check_health(
            http_server,
            metrics_server,
            grpc_server,
            trace_exporter,
            db_client,
            broker_consumer,
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
        grpc_server: ILifeCycle = Provide[Container.grpc_server],
        trace_exporter: ILifeCycle = Provide[Container.trace_exporter],
        db_client: ILifeCycle = Provide[Container.db_client],
        broker_consumer: ILifeCycle = Provide[Container.broker_consumer],
    ) -> None:
        logger.info("Stopping the app...")
        for component in (broker_consumer, grpc_server, db_client, metrics_server, http_server, trace_exporter):
            try:
                await component.stop()
            except Exception as error:
                logger.warning(
                    "An error occurred while stopping the %s: %s",
                    component.__class__.__name__,
                    error,
                )

        logger.info("The app has been stopped")
