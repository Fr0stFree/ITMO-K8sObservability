import asyncio
from http import HTTPMethod

from dependency_injector.wiring import Provide, inject

from common.http import IHTTPServer
from common.service import IService
from service_crawler.src.container import Container
from service_crawler.src.http import handlers


@inject
async def main(
    service: IService = Provide[Container.service],
    http_server: IHTTPServer = Provide[Container.http_server],
) -> None:
    http_server.add_handler(
        path="/health",
        handler=lambda request: handlers.health(request, service.is_healthy),
        method=HTTPMethod.GET,
    )
    await service.run()


if __name__ == "__main__":
    container = Container()
    container.wire(packages=["."], modules=[__name__])
    asyncio.run(main())
