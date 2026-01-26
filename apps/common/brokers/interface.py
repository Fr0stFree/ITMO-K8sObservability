from typing import Protocol


class IBrokerProducer(Protocol):
    async def send(self, message: bytes) -> None: ...
