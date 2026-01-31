from http import HTTPMethod
from typing import Protocol

from aiohttp.typedefs import Handler as IHttpHandler


class IHTTPServer(Protocol):
    def add_handler(self, path: str, handler: IHttpHandler, method: HTTPMethod) -> None: ...
    def add_middleware(self, middleware: IHttpHandler) -> None: ...
