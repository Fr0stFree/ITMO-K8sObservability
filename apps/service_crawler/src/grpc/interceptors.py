from typing import Any

from dependency_injector.wiring import Provide, inject
from grpc.aio import ServerInterceptor
from opentelemetry import context, propagate
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode
from prometheus_client import Histogram

from common.logs.interface import LoggerLike
from service_crawler.src.container import Container


# TODO: fix!!!
class ObservabilityServerInterceptor(ServerInterceptor):

    @inject
    async def intercept_service(
        self,
        continuation,
        handler_call_details,
        logger: LoggerLike = Provide[Container.logger],
        tracer: Tracer = Provide[Container.tracer],
        rpc_request_latency: Histogram = Provide[Container.rpc_request_latency],
    ) -> Any:
        self._extract_context(handler_call_details)
        method = (
            handler_call_details.method.decode()
            if isinstance(handler_call_details.method, bytes)
            else handler_call_details.method
        ).split("/")[-1]
        with tracer.start_as_current_span("grpc.server.request", attributes={"rpc.method": method}) as span:
            with rpc_request_latency.labels(method=method).time():
                logger.info("Received gRPC request for '%s'", method, extra={"method": method})
                try:
                    response = await continuation(handler_call_details)
                    logger.info("Successfully handled gRPC request for '%s'", method, extra={"method": method})
                    span.set_status(status=StatusCode.OK)
                    return response
                except Exception as error:
                    logger.error("gRPC request for '%s' failed: %s", method, str(error), extra={"method": method})
                    span.record_exception(error)
                    span.set_status(status=StatusCode.ERROR, description=str(error))
                    raise error

    # TODO: fix, deatach context after request handling
    def _extract_context(self, details: Any) -> None:
        metadata = dict(details.invocation_metadata)

        carrier = {}
        for k, v in metadata.items():
            carrier[k] = v

        ctx = propagate.extract(carrier)
        context.attach(ctx)
        print("Context extracted in server interceptor")
        print(f"Metadata: {metadata}")
