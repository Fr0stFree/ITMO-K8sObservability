from typing import MutableMapping
from common.brokers.interface import IConsumerInterceptor

from dependency_injector.wiring import Provide, inject

from opentelemetry.trace import Span, StatusCode
from opentelemetry.propagate import extract as extract_context
from opentelemetry.context import attach, detach
from common.logs.interface import LoggerLike
from service_analyzer.src.container import Container


_CONTEXT_TOKEN_KEY = "__otel_context_token__"


class ObservabilityConsumerInterceptor(IConsumerInterceptor):

    @inject
    async def before_receive(
        self,
        source: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        logger: LoggerLike = Provide[Container.logger],
    ) -> None:
        context = extract_context(meta)
        token = attach(context)
        meta[_CONTEXT_TOKEN_KEY] = token
        logger.info(f"Consuming message from '{source}'", extra={"destination": source})

    @inject
    async def after_receive(
        self,
        source: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> None:
        logger.info(f"Successfully consumed message from '{source}'", extra={"destination": source})
        span.set_status(StatusCode.OK)
        token = meta.pop(_CONTEXT_TOKEN_KEY, None)
        if token:
            detach(token)

    @inject
    async def on_error(
        self,
        source: str,
        payload: MutableMapping[str, str],
        meta: MutableMapping[str, str],
        exception: Exception,
        logger: LoggerLike = Provide[Container.logger],
        span: Span = Provide[Container.current_span],
    ) -> None:
        logger.error(
            f"Failed to consume message from '{source}': {exception}. Payload: {payload}",
            extra={"destination": source, "error": str(exception)},
        )
        span.record_exception(exception)
        span.set_status(StatusCode.ERROR)
        token = meta.pop(_CONTEXT_TOKEN_KEY, None)
        if token:
            detach(token)

