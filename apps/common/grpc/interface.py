from typing import Protocol

from grpc.aio import Server

type IServicer = object


class IGRPCClient(Protocol):
    def add_interceptor(self, interceptor) -> None: ...


class IServicerRegisterer(Protocol):
    def __call__(self, servicer: IServicer, server: Server) -> None: ...
