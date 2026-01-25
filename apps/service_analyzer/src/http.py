from collections.abc import Awaitable, Callable
from http import HTTPStatus

from aiohttp.web import Request, Response, json_response


async def health(request: Request, callback: Callable[[], Awaitable[bool]]) -> Response:
    result = await callback()
    if result:
        return json_response(status=HTTPStatus.OK)

    return json_response(status=HTTPStatus.GATEWAY_TIMEOUT)
