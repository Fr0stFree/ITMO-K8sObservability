from contextvars import Token
import time
from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc import unary_unary_rpc_method_handler
from grpc.aio import ServerInterceptor
from opentelemetry import propagate
from opentelemetry.context import attach, detach
from opentelemetry.metrics import Counter, Histogram
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode

from common.logs.interface import LoggerLike
from service_analyzer.src.container import Container


class ObservabilityServerInterceptor(ServerInterceptor):

    def _extract_context(self, details: Any) -> Token:
        metadata = dict(details.invocation_metadata)
        carrier = {k: v for k, v in metadata.items()}
        ctx = propagate.extract(carrier)
        token = attach(ctx)
        return token

    @inject
    async def intercept_service(
        self,
        continuation,
        handler_call_details,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        request_counter: Counter = Provide[Container.grpc_incoming_requests_counter],
        request_latency: Histogram = Provide[Container.grpc_incoming_requests_latency],
    ):
        method = (
            handler_call_details.method.decode()
            if isinstance(handler_call_details.method, bytes)
            else handler_call_details.method
        ).split("/")[-1]

        handler = await continuation(handler_call_details)
        if handler is None:
            return None

        def wrap_unary_unary(fn):
            async def new_behavior(request, grpc_context):
                token = None
                start = time.monotonic()
                attributes = {"method": method}
                token = self._extract_context(handler_call_details)

                try:
                    with tracer.start_as_current_span(
                        "grpc.server.request",
                        attributes={"rpc.method": method},
                    ) as span:
                        logger.info("Received gRPC request", extra=attributes)

                        try:
                            response = await fn(request, grpc_context)
                            span.set_status(StatusCode.OK)
                            attributes["status"] = StatusCode.OK.name
                            logger.info("Successfully handled gRPC request", extra=attributes)
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
                    detach(token)

            return new_behavior

        if handler.unary_unary:
            return unary_unary_rpc_method_handler(
                wrap_unary_unary(handler.unary_unary),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        return handler
