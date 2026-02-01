from grpc.aio import Channel, ClientInterceptor, insecure_channel

from common.logs import LoggerLike


class GRPCClient:
    def __init__(self, address: str, logger: LoggerLike) -> None:
        self._address = address
        self._logger = logger

        self._channel: Channel
        self._interceptors = []

    def add_interceptor(self, interceptor: ClientInterceptor) -> None:
        self._interceptors.append(interceptor)

    @property
    def channel(self) -> Channel:
        return self._channel

    async def start(self) -> None:
        self._logger.info("Creating gRPC channel to %s...", self._address)
        self._channel = insecure_channel(self._address, interceptors=self._interceptors)

    async def stop(self) -> None:
        self._logger.info("Closing gRPC channel to %s...", self._address)
        await self._channel.close()

    async def is_healthy(self) -> bool:
        # TODO: implement health check logic
        return True
