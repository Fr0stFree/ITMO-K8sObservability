from http import HTTPMethod
from typing import Protocol

from common.http.server import IHttpHandler


class IHTTPServer(Protocol):
    def add_handler(self, path: str, handler: IHttpHandler, method: HTTPMethod) -> None: ...
