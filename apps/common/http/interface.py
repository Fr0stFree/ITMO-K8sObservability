from http import HTTPMethod
from typing import Protocol

from aiohttp.typedefs import Handler as IHttpHandler
from aiohttp.typedefs import Middleware as IHttpMiddleware
from aiohttp.web import RouteTableDef


class IHTTPServer(Protocol):
    def add_handler(self, path: str, handler: IHttpHandler, method: HTTPMethod) -> None: ...
    def add_routes(self, routes: RouteTableDef) -> None: ...
    def add_middleware(self, middleware: IHttpMiddleware) -> None: ...
