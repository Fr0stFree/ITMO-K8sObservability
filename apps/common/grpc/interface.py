from typing import Protocol

from grpc.aio import ClientInterceptor, Server, ServerInterceptor

type IServicer = object


class IGRPCClient(Protocol):
    def add_interceptor(self, interceptor: ClientInterceptor) -> None: ...


class IGRPCServer(Protocol):
    def add_interceptor(self, interceptor: ServerInterceptor) -> None: ...


class IServicerRegisterer(Protocol):
    def __call__(self, servicer: IServicer, server: Server) -> None: ...
