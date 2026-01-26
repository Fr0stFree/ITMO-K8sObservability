from typing import Protocol


class ILifeCycle(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


class IHealthCheck(Protocol):
    async def is_healthy(self) -> bool: ...
