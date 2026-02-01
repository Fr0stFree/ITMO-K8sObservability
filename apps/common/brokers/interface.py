from abc import ABC
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Protocol


class IProducerInterceptor(ABC):
    async def before_send(
        self, destination: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str]
    ) -> None:
        pass

    async def after_send(
        self, destination: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str]
    ) -> None:
        pass

    async def on_error(
        self, destination: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str], exception: Exception
    ) -> None:
        pass


class IConsumerInterceptor(ABC):
    async def before_receive(
        self, source: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str]
    ) -> None:
        pass

    async def after_receive(
        self, source: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str]
    ) -> None:
        pass

    async def on_error(
        self, source: str, payload: MutableMapping[str, str], meta: MutableMapping[str, str], exception: Exception
    ) -> None:
        pass


class IBrokerProducer(Protocol):
    async def send(self, message: dict, meta: dict) -> None: ...
    def add_interceptor(self, interceptor: IProducerInterceptor) -> None: ...


class IBrokerConsumer(Protocol):
    def set_message_handler(self, on_message: Callable[[dict], Awaitable[None]]) -> None: ...
    def add_interceptor(self, interceptor: IConsumerInterceptor) -> None: ...