from typing import Protocol

from grpc.aio import ClientInterceptor, Server, ServerInterceptor


class IRPCServicer(Protocol):
    def add_to_server(self, server: Server) -> None: ...


class IGRPCClient(Protocol):
    def add_interceptor(self, interceptor: ClientInterceptor) -> None: ...


class IGRPCServer(Protocol):
    def add_interceptor(self, interceptor: ServerInterceptor) -> None: ...
    def setup_servicer(self, servicer: IRPCServicer) -> None: ...
