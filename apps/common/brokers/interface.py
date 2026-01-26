from collections.abc import Awaitable, Callable
from typing import Protocol


class IBrokerProducer(Protocol):
    async def send(self, message: dict) -> None: ...


class IBrokerConsumer(Protocol):
    def set_message_handler(self, on_message: Callable[[dict], Awaitable[None]]) -> None: ...
