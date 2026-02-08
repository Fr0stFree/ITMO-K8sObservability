import asyncio

from dependency_injector.wiring import Provide, inject

from common.grpc import IGRPCClient
from common.http import IHTTPServer
from common.service import IService
from service_api.src.container import Container
from service_api.src.grpc import interceptors
from service_api.src.http import handlers, middleware


@inject
async def main(
    http_server: IHTTPServer = Provide[Container.http_server],
    crawler_client: IGRPCClient = Provide[Container.crawler_client],
    analyzer_client: IGRPCClient = Provide[Container.analyzer_client],
    service: IService = Provide[Container.service],
) -> None:
    http_server.add_routes(handlers.routes)
    http_server.add_middleware(middleware.tracing)
    http_server.add_middleware(middleware.logging)
    http_server.add_middleware(middleware.metrics)
    http_server.add_middleware(middleware.error_handling)
    crawler_client.add_interceptor(interceptors.TracingClientInterceptor())
    analyzer_client.add_interceptor(interceptors.LoggingClientInterceptor())
    analyzer_client.add_interceptor(interceptors.MetricsClientInterceptor())

    await service.run()


if __name__ == "__main__":
    container = Container()
    container.wire(packages=["."], modules=[__name__])
    asyncio.run(main())
