from collections.abc import Awaitable, Callable
import time
from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc.aio import ClientCallDetails, UnaryUnaryClientInterceptor
from opentelemetry import propagate
from opentelemetry.metrics import Counter, Histogram
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode

from common.logs.interface import LoggerLike
from service_api.src.container import Container

type UnaryUnaryContinuation = Callable[
    [ClientCallDetails, Any],
    Awaitable[Any],
]


def _retrieve_method_name(details: ClientCallDetails) -> str:
    return (details.method.decode() if isinstance(details.method, bytes) else details.method).split("/")[-1]


class LoggingClientInterceptor(UnaryUnaryClientInterceptor):

    @inject
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuation,
        client_call_details: ClientCallDetails,
        request: Any,
        logger: LoggerLike = Provide[Container.logger],
    ) -> Any:
        method = _retrieve_method_name(client_call_details)
        logger.info("Making gRPC request to '%s'", method, extra={"method": method})
        try:
            result = await continuation(client_call_details, request)
            logger.info("Received gRPC response from '%s'", method, extra={"method": method})
            return result
        except Exception as error:
            logger.error("gRPC request to '%s' failed: %s", method, str(error), extra={"method": method})
            raise error


class MetricsClientInterceptor(UnaryUnaryClientInterceptor):
    @inject
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuation,
        client_call_details: ClientCallDetails,
        request: Any,
        request_counter: Counter = Provide[Container.grpc_outgoing_requests_counter],
        request_latency: Histogram = Provide[Container.grpc_outgoing_requests_latency],
    ) -> Any:
        attributes = {"method": _retrieve_method_name(client_call_details)}
        start = time.monotonic()
        try:
            return await continuation(client_call_details, request)
        finally:
            duration = time.monotonic() - start
            request_latency.record(duration, attributes)
            request_counter.add(1, attributes)


class TracingClientInterceptor(UnaryUnaryClientInterceptor):
    @inject
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuation,
        client_call_details: ClientCallDetails,
        request: Any,
        tracer: Tracer = Provide[Container.tracer],
    ) -> Any:
        details = self._inject_context(client_call_details)
        method = _retrieve_method_name(details)
        with tracer.start_as_current_span("grpc.client.request", attributes={"rpc.method": method}) as span:
            try:
                result = await continuation(details, request)
                span.set_status(status=StatusCode.OK)
                return result
            except Exception as error:
                span.record_exception(error)
                span.set_status(status=StatusCode.ERROR, description=str(error))
                raise error

    def _inject_context(self, client_call_details: ClientCallDetails) -> ClientCallDetails:
        metadata = []
        if client_call_details.metadata:
            metadata = list(client_call_details.metadata)

        carrier = {}
        propagate.inject(carrier)

        for k, v in carrier.items():
            metadata.append((k, v))

        details = client_call_details._replace(metadata=metadata)
        return details
