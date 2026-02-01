import asyncio
from collections.abc import Iterable
import signal

from common.logs import LoggerLike
from common.service.interface import IServiceComponent
from common.service.settings import ServiceSettings
from common.utils.health import check_health


class BaseService:
    def __init__(self, components: Iterable[IServiceComponent], logger: LoggerLike, settings: ServiceSettings) -> None:
        self._components = components
        self._logger = logger
        self._settings = settings

    async def run(self) -> None:
        self._logger.info("Starting the %s...", self._settings.name)
        running = asyncio.Event()
        for component in self._components:
            await component.start()
        self._logger.info("The %s has been started", self._settings.name)

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, running.set)
        loop.add_signal_handler(signal.SIGTERM, running.set)

        await running.wait()
        await self._stop()

    async def is_healthy(self) -> bool:
        result = await check_health(*self._components, timeout=self._settings.health_check_timeout)
        self._logger.info(
            "Health check result: %s",
            ", ".join(f"{comp.__class__.__name__}: {status}" for comp, status in result.items()),
        )
        return all(result.values())

    async def _stop(self) -> None:
        self._logger.info("Stopping the %s...", self._settings.name)
        for component in self._components:
            try:
                await component.stop()
            except Exception as error:
                self._logger.warning("An error occurred while stopping the %s: %s", component.__class__.__name__, error)

        self._logger.info("The %s has been stopped", self._settings.name)
