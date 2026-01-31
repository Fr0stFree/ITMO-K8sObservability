from collections.abc import Awaitable, Callable
from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web import Request, Response, json_response
from dependency_injector.wiring import Provide, inject
from google.protobuf.json_format import MessageToDict

from protocol.analyzer_pb2 import GetTargetDetailsRequest
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
from protocol.crawler_pb2 import AddTargetRequest
from protocol.crawler_pb2_grpc import CrawlerServiceStub
from service_api.src.container import Container


async def health(request: Request, callback: Callable[[], Awaitable[bool]]) -> Response:
    result = await callback()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)


@inject
async def add_target(request: Request, crawler_stub: CrawlerServiceStub = Provide[Container.crawler_stub]) -> Response:
    try:
        body = await request.json()
    except JSONDecodeError:
        return Response(text="Invalid JSON body", status=HTTPStatus.BAD_REQUEST)

    target_url = body.get("targetUrl")
    if not target_url:
        return Response(text="missing targetUrl field", status=HTTPStatus.BAD_REQUEST)

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
        return Response(text="missing url id in path", status=HTTPStatus.BAD_REQUEST)

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
