import asyncio
from http import HTTPMethod

from common.http import IHTTPServer
from common.service import IService
from common.tracing.context.grpc import OpenTelemetryClientInterceptor
from service_api.src.container import Container
from service_api.src.grpc import interceptors

from dependency_injector.wiring import Provide, inject
from common.grpc import IGRPCClient
from service_api.src.http import handlers, middleware


@inject
async def main(
    http_server: IHTTPServer = Provide[Container.http_server],
    crawler_client: IGRPCClient = Provide[Container.crawler_client],
    service: IService = Provide[Container.service],
) -> None:
    http_server.add_middleware(middleware.observability)
    http_server.add_handler(
        path="/health",
        handler=lambda request: handlers.health(request, service.is_healthy),
        method=HTTPMethod.GET,
    )
    http_server.add_handler(
        path="/targets",
        handler=handlers.add_target,
        method=HTTPMethod.POST,
    )
    http_server.add_handler(
        path="/targets/{target_id}",
        handler=handlers.get_target,
        method=HTTPMethod.GET,
    )
    http_server.add_handler(
        path="/targets",
        handler=handlers.list_targets,
        method=HTTPMethod.GET,
    )
    http_server.add_handler(
        path="/targets/{target_id}",
        handler=handlers.delete_target,
        method=HTTPMethod.DELETE,
    )
    crawler_client.add_interceptor(OpenTelemetryClientInterceptor())
    crawler_client.add_interceptor(interceptors.ObservabilityClientInterceptor())

    await service.run()


if __name__ == "__main__":
    container = Container()
    container.wire(packages=["."], modules=[__name__])
    asyncio.run(main())
