from http import HTTPStatus

from aiohttp import web
from aiohttp.typedefs import Handler as IHttpHandler
from grpc.aio import AioRpcError
from grpc import StatusCode
from dependency_injector.wiring import Provide, inject
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode as TraceStatusCode
from prometheus_client import Counter, Histogram

from common.logs.interface import LoggerLike
from service_api.src.container import Container


@web.middleware
@inject
async def error_handling(
    request: web.Request,
    handler: IHttpHandler,
) -> web.StreamResponse:
    try:
        return await handler(request)
    except AioRpcError as error:
        match error.code():
            case StatusCode.NOT_FOUND:
                return web.json_response(
                    data={"error": error.details()},
                    status=HTTPStatus.NOT_FOUND,
                )
            case StatusCode.INVALID_ARGUMENT:
                return web.json_response(
                    data={"error": error.details()},
                    status=HTTPStatus.BAD_REQUEST,
                )
            case StatusCode.UNAVAILABLE:
                return web.json_response(
                    {"error": "Upstream service is unavailable"},
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                )
            case _:
                return web.json_response(
                    data={"error": "Internal server error"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )


@web.middleware
@inject
async def observability(
    request: web.Request,
    handler: IHttpHandler,
    logger: LoggerLike = Provide[Container.logger],
    tracer: Tracer = Provide[Container.tracer],
    request_counter: Counter = Provide[Container.requests_counter],
    request_latency: Histogram = Provide[Container.request_latency],
) -> web.StreamResponse:
    with tracer.start_as_current_span(
        "http.request", attributes={"http.method": request.method, "http.endpoint": request.path}
    ) as span:
        with request_latency.labels(method=request.method, endpoint=request.path).time():
            logger.info(
                "Processing %s request for %s",
                request.method,
                request.path,
                extra={"path": request.path, "method": request.method},
            )
            try:
                response = await handler(request)
            except Exception as error:
                request_counter.labels(
                    method=request.method,
                    endpoint=request.path,
                    http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
                ).inc()
                logger.error(
                    "Failed to process %s request for %s: %s",
                    request.method,
                    request.path,
                    str(error),
                    extra={"path": request.path, "method": request.method, "status": HTTPStatus.INTERNAL_SERVER_ERROR},
                )
                span.record_exception(error)
                span.set_status(status=TraceStatusCode.ERROR, description=str(error))
                raise error

            request_counter.labels(method=request.method, endpoint=request.path, http_status=response.status).inc()
            logger.info(
                "Successfully processed %s request for %s, response status: %d",
                request.method,
                request.path,
                response.status,
                extra={"path": request.path, "method": request.method, "status": response.status},
            )
            span.set_attribute("http.status_code", response.status)
            span.set_status(status=TraceStatusCode.OK)
            return response
