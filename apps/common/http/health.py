import asyncio
import datetime as dt
from http import HTTPStatus

from aiohttp.web import Request, Response, json_response

from common.logs.logger import LoggerLike
from common.types.protocol import IHealthCheck


class HealthHandler:
    def __init__(
        self,
        *components: IHealthCheck,
        logger: LoggerLike,
        timeout: dt.timedelta = dt.timedelta(seconds=2),
    ) -> None:
        self._components = components
        self._logger = logger
        self._timeout = timeout

    async def __call__(self, request: Request) -> Response:
        checks = {component.__class__.__name__: component.is_healthy() for component in self._components}
        results = await asyncio.wait_for(
            asyncio.gather(*checks.values(), return_exceptions=True), timeout=self._timeout.total_seconds()
        )

        body, alive, dead = {}, [], []
        for name, result in zip(checks.keys(), results):
            is_alive = False if isinstance(result, Exception) else result
            body[name] = is_alive
            if is_alive:
                alive.append(name)
            else:
                dead.append(name)

        self._logger.info("Health check result - alive: %s. dead: %s.", ", ".join(alive), ", ".join(dead))
        if not dead:
            return json_response(body, status=HTTPStatus.OK)

        return json_response(body, status=HTTPStatus.GATEWAY_TIMEOUT)
