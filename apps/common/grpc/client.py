from grpc.aio import ClientInterceptor, insecure_channel

from common.logs import LoggerLike


class GRPCClient[V]:
    def __init__(self, address: str, stub_class: type[V], logger: LoggerLike) -> None:
        self._address = address
        self._logger = logger
        self._stub_class = stub_class

        self._interceptors = []

    def add_interceptor(self, interceptor: ClientInterceptor) -> None:
        self._interceptors.append(interceptor)

    async def __aenter__(self) -> V:
        self._channel = insecure_channel(self._address, interceptors=self._interceptors)
        self._stub = self._stub_class(self._channel)
        return self._stub

    async def __aexit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb) -> None:
        await self._channel.close()
