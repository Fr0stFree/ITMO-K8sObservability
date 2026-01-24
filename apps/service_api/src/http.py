import asyncio
import datetime as dt
from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject

from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from protocol.crawler_pb2 import AddTargetRequest
from protocol.crawler_pb2_grpc import CrawlerServiceStub
from service_api.src.container import Container


@inject
async def health(
    request: Request,
    health_check_timeout: dt.timedelta = Provide[Container.settings.health_check_timeout],
    logger: LoggerLike = Provide[Container.logger],
    http_server: HTTPServer = Provide[Container.http_server],
    metrics_server: MetricsServer = Provide[Container.metrics_server],
    crawler_client: GRPCClient = Provide[Container.crawler_client],
) -> Response:
    components = (http_server, metrics_server, crawler_client)
    checks = {component.__class__.__name__: component.is_healthy() for component in components}
    results = await asyncio.wait_for(
        asyncio.gather(*checks.values(), return_exceptions=True),
        timeout=health_check_timeout.total_seconds(),
    )

    body, alive, dead = {}, [], []
    for name, result in zip(checks.keys(), results):
        is_alive = False if isinstance(result, Exception) else result
        body[name] = is_alive
        if is_alive:
            alive.append(name)
        else:
            dead.append(name)

    logger.info("Health check result - alive: %s. dead: %s.", ", ".join(alive), ", ".join(dead))
    if not dead:
        return json_response(body, status=HTTPStatus.OK)

    return json_response(body, status=HTTPStatus.GATEWAY_TIMEOUT)


@inject
async def add_target(
    request: Request,
    crawler_stub: CrawlerServiceStub = Provide[Container.crawler_stub],
) -> Response:
    try:
        body = await request.json()
    except JSONDecodeError:
        return Response(text="Invalid JSON body", status=HTTPStatus.BAD_REQUEST)

    body = await request.json()
    target_url = body.get("target_url")
    if not target_url:
        return Response(text="missing target_url field", status=HTTPStatus.BAD_REQUEST)

    request = AddTargetRequest(target_url=target_url)
    await crawler_stub.AddTarget(request)
    return Response(status=HTTPStatus.CREATED)
