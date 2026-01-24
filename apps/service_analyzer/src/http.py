import datetime as dt
from http import HTTPStatus

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject

from common.databases.postgres.client import PostgresClient
from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from common.tracing.exporter import TraceExporter
from common.utils.health import check_health
from service_analyzer.src.container import Container


@inject
async def health(
    request: Request,
    health_check_timeout: dt.timedelta = Provide[Container.settings.health_check_timeout],
    logger: LoggerLike = Provide[Container.logger],
    http_server: HTTPServer = Provide[Container.http_server],
    metrics_server: MetricsServer = Provide[Container.metrics_server],
    grpc_server: GRPCClient = Provide[Container.grpc_server],
    trace_exporter: TraceExporter = Provide[Container.trace_exporter],
    db_client: PostgresClient = Provide[Container.db_client],
) -> Response:
    result = await check_health(
        http_server,
        metrics_server,
        grpc_server,
        trace_exporter,
        db_client,
        timeout=health_check_timeout,
    )
    logger.info("Health check result: %s", result)

    if all(result.values()):
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)
