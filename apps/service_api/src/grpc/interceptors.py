from collections.abc import Awaitable, Callable
from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc.aio import ClientCallDetails, UnaryUnaryClientInterceptor
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode
from prometheus_client import Histogram

from common.logs.interface import LoggerLike
from service_api.src.container import Container
from opentelemetry import propagate

type UnaryUnaryContinuation = Callable[
    [ClientCallDetails, Any],
    Awaitable[Any],
]


class ObservabilityClientInterceptor(UnaryUnaryClientInterceptor):

    @inject
    async def intercept_unary_unary(
        self,
        continuation: UnaryUnaryContinuation,
        client_call_details: ClientCallDetails,
        request: Any,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        rpc_request_latency: Histogram = Provide[Container.rpc_request_latency],
    ) -> Any:
        details = self._inject_context(client_call_details)
        method = (
            details.method.decode()
            if isinstance(details.method, bytes)
            else details.method
        ).split("/")[-1]
        with tracer.start_as_current_span("grpc.client.request", attributes={"rpc.method": method}) as span:
            with rpc_request_latency.labels(method=method).time():
                logger.info("Making gRPC request to '%s'", method, extra={"method": method})
                try:
                    result = await continuation(details, request)
                    logger.info("Received gRPC response from '%s'", method, extra={"method": method})
                    span.set_status(status=StatusCode.OK)
                    return result
                except Exception as error:
                    logger.error("gRPC request to '%s' failed: %s", method, str(error), extra={"method": method})
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
