import asyncio
import datetime as dt
from http import HTTPStatus

from aiohttp.web import Request, json_response, Response
from dependency_injector.wiring import Provide, inject

from common.grpc.server import GRPCServer
from common.http.server import HTTPServer
from common.logs.logger import LoggerLike
from common.metrics.server import MetricsServer
from monitoring_service.src.container import Container


@inject
async def health(
    request: Request,
    healthcheck_timeout: dt.timedelta = Provide[Container.config.health_check_timeout],
    logger: LoggerLike = Provide[Container.logger],
    http_server: HTTPServer = Provide[Container.http_server],
    metrics_server: MetricsServer = Provide[Container.metrics_server],
    grpc_server: GRPCServer = Provide[Container.grpc_server],
) -> Response:
    checks = {
        component.__class__.__name__: component.is_healthy() for component in (http_server, metrics_server, grpc_server)
    }
    results = await asyncio.wait_for(
        asyncio.gather(*checks.values(), return_exceptions=True), timeout=healthcheck_timeout.total_seconds()
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
