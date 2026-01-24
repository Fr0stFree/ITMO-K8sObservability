import datetime as dt
from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject
from google.protobuf.json_format import MessageToDict

from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerLike
from common.metrics import MetricsServer
from common.tracing.exporter import TraceExporter
from common.utils.health import check_health
from protocol.analyzer_pb2 import GetTargetDetailsRequest
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
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
    trace_exporter: TraceExporter = Provide[Container.trace_exporter],
    crawler_client: GRPCClient = Provide[Container.crawler_client],
    analyzer_client: GRPCClient = Provide[Container.analyzer_client],
) -> Response:
    result = await check_health(
        http_server,
        metrics_server,
        crawler_client,
        analyzer_client,
        trace_exporter,
        timeout=health_check_timeout,
    )
    logger.info("Health check result: %s", result)

    if all(result.values()):
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


@inject
async def add_target(
    request: Request,
    crawler_stub: CrawlerServiceStub = Provide[Container.crawler_stub],
) -> Response:
    try:
        body = await request.json()
    except JSONDecodeError:
        return Response(text="Invalid JSON body", status=HTTPStatus.BAD_REQUEST)

    target_url = body.get("target_url")
    if not target_url:
        return Response(text="missing target_url field", status=HTTPStatus.BAD_REQUEST)

    rpc_request = AddTargetRequest(target_url=target_url)
    await crawler_stub.AddTarget(rpc_request)
    return Response(status=HTTPStatus.CREATED)


@inject
async def get_target(
    request: Request,
    analyzer_stub: AnalyzerServiceStub = Provide[Container.analyzer_stub],
) -> Response:
    target_id = request.match_info.get("target_id")
    if not target_id:
        return Response(text="missing target_id in path", status=HTTPStatus.BAD_REQUEST)

    rpc_request = GetTargetDetailsRequest(id=target_id)
    rpc_response = await analyzer_stub.GetTargetDetails(rpc_request)
    response_body = MessageToDict(rpc_response, preserving_proto_field_name=True)
    return json_response(response_body, status=HTTPStatus.OK)


@inject
async def list_targets(request: Request) -> Response:
    raise NotImplementedError("Not implemented yet")


@inject
async def delete_target(request: Request) -> Response:
    raise NotImplementedError("Not implemented yet")
