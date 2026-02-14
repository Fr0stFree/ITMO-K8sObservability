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


class ObservabilityClientInterceptor(UnaryUnaryClientInterceptor):

    def _inject_context(self, client_call_details: ClientCallDetails) -> ClientCallDetails:
        metadata = list(client_call_details.metadata or [])

        carrier = {}
        propagate.inject(carrier)

        for k, v in carrier.items():
            metadata.append((k, v))

        return client_call_details._replace(metadata=metadata)

    @inject
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuation,
        client_call_details: ClientCallDetails,
        request: Any,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        request_counter: Counter = Provide[Container.grpc_outgoing_requests_counter],
        request_latency: Histogram = Provide[Container.grpc_outgoing_requests_latency],
    ) -> Any:

        method = _retrieve_method_name(client_call_details)
        attributes = {"method": method}
        start = time.monotonic()
        details = self._inject_context(client_call_details)
        with tracer.start_as_current_span(
            "grpc.client.request",
            attributes={"rpc.method": method},
        ) as span:
            logger.info("Making gRPC request", extra=attributes)
            try:
                call = await continuation(details, request)
                response = await call
                span.set_status(StatusCode.OK)
                attributes["status"] = StatusCode.OK.name
                logger.info("Received gRPC response", extra=attributes)
                return response
            except Exception as error:
                span.record_exception(error)
                span.set_status(StatusCode.ERROR, str(error))
                attributes["status"] = StatusCode.ERROR.name
                logger.exception("gRPC request failed", extra=attributes)
                raise error
            finally:
                duration = time.monotonic() - start
                request_latency.record(duration, attributes)
                request_counter.add(1, attributes)
