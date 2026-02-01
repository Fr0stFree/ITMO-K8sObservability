from http import HTTPStatus
from dependency_injector.wiring import Provide, inject
from aiohttp.web import Request, Response, json_response
from common.service import IService
from service_analyzer.src.container import Container


@inject
async def health(request: Request, service: IService = Provide[Container.service]) -> Response:
    is_healthy = await service.is_healthy()
    if is_healthy:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)
