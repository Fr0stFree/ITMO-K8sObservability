from collections.abc import Awaitable, Callable
from typing import Protocol

from aiokafka import ConsumerRecord


class IBrokerProducer(Protocol):
    async def send(self, message: bytes) -> None: ...


class IBrokerConsumer(Protocol):
    def set_message_handler(self, on_message: Callable[[ConsumerRecord], Awaitable[None]]) -> None: ...
