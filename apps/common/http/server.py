from http import HTTPMethod

from aiohttp.typedefs import Handler as IHttpHandler
from aiohttp.typedefs import Middleware as IHttpMiddleware
from aiohttp.web import Application, AppRunner, RouteTableDef, TCPSite

from common.http.settings import HTTPServerSettings
from common.logs import LoggerLike


class HTTPServer:
    def __init__(self, settings: HTTPServerSettings, logger: LoggerLike) -> None:
        self._settings = settings
        self._logger = logger
        self._app = Application(logger=logger)
        self._runner = AppRunner(self._app)

        self._site: TCPSite

    def add_middleware(self, middleware: IHttpMiddleware) -> None:
        self._logger.info("Registering HTTP middleware '%s'", middleware.__name__)
        self._app.middlewares.append(middleware)

    def add_handler(self, path: str, handler: IHttpHandler, method: HTTPMethod) -> None:
        self._logger.info(
            "Registering HTTP-%s handler '%s'",
            method,
            path,
            extra={"path": path, "method": method},
        )
        self._app.router.add_route(method, path, handler)

    def add_routes(self, routes: RouteTableDef) -> None:
        self._logger.info("Registering %d HTTP routes", len(routes))
        self._app.add_routes(routes)

    async def is_healthy(self) -> bool:
        return self._runner.server is not None

    async def start(self) -> None:
        self._logger.info("Starting the http server on port %d...", self._settings.port)
        await self._runner.setup()
        self._site = TCPSite(self._runner, "0.0.0.0", self._settings.port)
        await self._site.start()

    async def stop(self) -> None:
        self._logger.info("Shutting down the http server...")
        await self._site.stop()
        await self._runner.shutdown()
        await self._app.cleanup()
