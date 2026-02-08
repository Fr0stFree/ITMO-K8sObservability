from http import HTTPStatus

from aiohttp import web
from aiohttp.typedefs import Handler as IHttpHandler
from attr import attributes
from dependency_injector.wiring import Provide, inject
from grpc import StatusCode
from grpc.aio import AioRpcError
from opentelemetry.trace import Tracer
from opentelemetry.trace.status import StatusCode as TraceStatusCode
from prometheus_client import Counter, Histogram
from opentelemetry.metrics import Counter as OTelCounter
from common.logs.interface import LoggerLike
from service_api.src.container import Container


@web.middleware
async def error_handling(request: web.Request, handler: IHttpHandler) -> web.StreamResponse:
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
        raise error


def _retrieve_canonical_path(request: web.Request) -> str:
    route = request.match_info.route
    if route is not None and route.resource is not None:
        return route.resource.canonical
    return request.path


@web.middleware
@inject
async def logging(
    request: web.Request,
    handler: IHttpHandler,
    logger: LoggerLike = Provide[Container.logger],
) -> web.StreamResponse:
    logger.info(
        "Received %s request for %s",
        request.method,
        request.path,
        extra={"path": request.path, "method": request.method},
    )
    try:
        response = await handler(request)
    except Exception as error:
        logger.error(
            "Failed to process %s request for %s: %s",
            request.method,
            request.path,
            str(error),
            extra={"path": request.path, "method": request.method, "status": HTTPStatus.INTERNAL_SERVER_ERROR},
        )
        raise error

    logger.info(
        "Responding to %s request for %s with status %d",
        request.method,
        request.path,
        response.status,
        extra={"path": request.path, "method": request.method, "status": response.status},
    )
    return response


@web.middleware
@inject
async def metrics(
    request: web.Request,
    handler: IHttpHandler,
    request_counter: Counter = Provide[Container.requests_counter],
    request_latency: Histogram = Provide[Container.request_latency],
    requests_counter_otel: OTelCounter = Provide[Container.requests_counter_otel],
) -> web.StreamResponse:
    canonical_path = _retrieve_canonical_path(request)
    attributes = {"method": request.method, "endpoint": canonical_path}
    with request_latency.labels(method=request.method, endpoint=canonical_path).time():
        try:
            response = await handler(request)
        except Exception as error:
            attributes["http_status"] = str(HTTPStatus.INTERNAL_SERVER_ERROR)
            request_counter.labels(**attributes).inc()
            requests_counter_otel.add(1, attributes)
            raise error

        attributes["http_status"] = str(response.status)
        requests_counter_otel.add(1, attributes)
        request_counter.labels(**attributes).inc()
        return response


@web.middleware
@inject
async def tracing(
    request: web.Request,
    handler: IHttpHandler,
    tracer: Tracer = Provide[Container.tracer],
) -> web.StreamResponse:
    with tracer.start_as_current_span(
        "http.request", attributes={"http.method": request.method, "http.endpoint": request.path}
    ) as span:
        try:
            response = await handler(request)
        except Exception as error:
            span.record_exception(error)
            span.set_status(status=TraceStatusCode.ERROR, description=str(error))
            raise error

        span.set_attribute("http.status_code", response.status)
        span.set_status(status=TraceStatusCode.OK)
        return response
