import datetime as dt
from http import HTTPStatus

from aiohttp.web import Request, Response, json_response
from common.utils.health import check_health
from service_crawler.src.url_crawler import CrawlerPool
from service_crawler.src.url_dumper import URLDumper
from dependency_injector.wiring import Provide, inject

from common.databases.postgres import PostgresClient
from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from service_crawler.src.container import Container


@inject
async def health(
    request: Request,
    health_check_timeout: dt.timedelta = Provide[Container.settings.health_check_timeout],
    logger: LoggerLike = Provide[Container.logger],
    http_server: HTTPServer = Provide[Container.http_server],
    metrics_server: MetricsServer = Provide[Container.metrics_server],
    grpc_server: GRPCServer = Provide[Container.grpc_server],
    crawler_pool: CrawlerPool = Provide[Container.crawler_pool],
    dumper: URLDumper = Provide[Container.dumper],
) -> Response:
    result = await check_health(
        http_server,
        metrics_server,
        grpc_server,
        crawler_pool,
        dumper,
        timeout=health_check_timeout,
    )
    logger.info("Health check result: %s", ", ".join(f"{k.__class__.__name__}: {v}" for k, v in result.items()))

    if all(result.values()):
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


