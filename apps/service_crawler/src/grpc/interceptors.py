from contextvars import Token
import time
from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc.aio import ServerInterceptor
from opentelemetry import context, propagate
from opentelemetry.context import Context
from opentelemetry.metrics import Counter, Histogram
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode

from common.logs.interface import LoggerLike
from service_crawler.src.container import Container


class ObservabilityServerInterceptor(ServerInterceptor):

    @inject
    async def intercept_service(
        self,
        continuation,
        handler_call_details,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        request_counter: Counter = Provide[Container.grpc_incoming_requests_counter],
        request_latency: Histogram = Provide[Container.grpc_incoming_requests_latency],
    ) -> Any:
        token = self._extract_context(handler_call_details)
        start = time.monotonic()
        method = (
            handler_call_details.method.decode()
            if isinstance(handler_call_details.method, bytes)
            else handler_call_details.method
        ).split("/")[-1]
        attributes = {"method": method}
        try:
            with tracer.start_as_current_span("grpc.server.request", attributes={"rpc.method": method}) as span:
                logger.info("Received gRPC request for '%s'", method, extra={"method": method})
                try:
                    response = await continuation(handler_call_details)
                    logger.info("Successfully handled gRPC request for '%s'", method, extra={"method": method})
                    span.set_status(status=StatusCode.OK)
                    attributes["status"] = StatusCode.OK.name
                    return response
                except Exception as error:
                    logger.error("gRPC request for '%s' failed: %s", method, str(error), extra={"method": method})
                    span.record_exception(error)
                    span.set_status(status=StatusCode.ERROR, description=str(error))
                    attributes["status"] = StatusCode.ERROR.name
                    raise error
        finally:
            duration = time.monotonic() - start
            request_latency.record(duration, attributes)
            request_counter.add(1, attributes)
            context.detach(token)

    def _extract_context(self, details: Any) -> Token[Context]:
        metadata = dict(details.invocation_metadata)

        carrier = {}
        for k, v in metadata.items():
            carrier[k] = v

        ctx = propagate.extract(carrier)
        token = context.attach(ctx)
        return token
