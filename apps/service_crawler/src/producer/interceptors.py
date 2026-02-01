from collections.abc import MutableMapping

from dependency_injector.wiring import Provide, inject
from opentelemetry.propagate import inject as inject_context
from opentelemetry.trace import Span
from opentelemetry.trace.status import StatusCode

from common.brokers.interface import IProducerInterceptor
from common.logs.interface import LoggerLike
from service_crawler.src.container import Container


class ObservabilityProducerInterceptor(IProducerInterceptor):

    @inject
    async def before_send(
        self,
        destination: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        span: Span = Provide[Container.current_span],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        span.set_attribute("messaging.destination", destination)
        inject_context(meta)
        logger.info(f"Producing message to '{destination}'...", extra={"destination": destination})

    @inject
    async def after_send(
        self,
        destination: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> None:
        logger.info(f"Successfully produced message to '{destination}'.", extra={"destination": destination})
        span.set_status(StatusCode.OK)

    @inject
    async def on_error(
        self,
        destination: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        exception: Exception,
        span: Span = Provide[Container.current_span],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        logger.error(
            f"Failed to produce message to '{destination}': {exception}. Payload: {payload}",
            extra={"destination": destination, "error": str(exception)},
        )
        span.record_exception(exception)
        span.set_status(StatusCode.ERROR)
