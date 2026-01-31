from collections.abc import Awaitable, Callable
from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc.aio import ClientCallDetails, UnaryUnaryClientInterceptor
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode
from prometheus_client import Histogram

from common.logs.interface import LoggerLike
from service_api.src.container import Container

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
        method = (
            client_call_details.method.decode()
            if isinstance(client_call_details.method, bytes)
            else client_call_details.method
        ).split("/")[-1]
        with tracer.start_as_current_span("grpc.client.request", attributes={"rpc.method": method}) as span:
            with rpc_request_latency.labels(method=method).time():
                logger.info("Making gRPC request to '%s'", method, extra={"method": method})
                try:
                    result = await continuation(client_call_details, request)
                    logger.info("Received gRPC response from '%s'", method, extra={"method": method})
                    span.set_status(status=StatusCode.OK)
                    return result
                except Exception as error:
                    logger.error("gRPC request to '%s' failed: %s", method, str(error), extra={"method": method})
                    span.record_exception(error)
                    span.set_status(status=StatusCode.ERROR, description=str(error))
                    raise error
