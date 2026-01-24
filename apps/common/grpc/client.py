from grpc.aio import Channel, insecure_channel

from common.grpc.settings import GRPCClientSettings
from common.logs.logger import LoggerLike


class GRPCClient:
    def __init__(self, settings: GRPCClientSettings, stub_class: type, logger: LoggerLike) -> None:
        self._settings = settings
        self._logger = logger
        self._stub_class = stub_class

        self._channel: Channel

    @property
    def stub(self) -> object:
        return self._stub

    async def start(self) -> None:
        self._logger.info("Creating gRPC channel to %s...", self._settings.address)
        self._channel = insecure_channel(self._settings.address)
        self._stub = self._stub_class(self._channel)

    async def stop(self) -> None:
        self._logger.info("Closing gRPC channel...")
        await self._channel.close()

    async def is_healthy(self) -> bool:
        # TODO: implement health check logic
        return True
