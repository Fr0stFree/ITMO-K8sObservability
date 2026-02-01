import asyncio
from http import HTTPMethod

from dependency_injector.wiring import Provide, inject

from common.brokers.interface import IBrokerProducer
from common.grpc.interface import IGRPCServer
from common.http import IHTTPServer
from common.service import IService
from common.tracing.context.grpc import OpenTelemetryServerInterceptor
from service_crawler.src.container import Container
from service_crawler.src.grpc.interceptors import ObservabilityServerInterceptor
from service_crawler.src.http import handlers
from service_crawler.src.producer.interceptors import ObservabilityProducerInterceptor


@inject
async def main(
    service: IService = Provide[Container.service],
    http_server: IHTTPServer = Provide[Container.http_server],
    grpc_server: IGRPCServer = Provide[Container.grpc_server],
    producer: IBrokerProducer = Provide[Container.broker_producer],
) -> None:
    http_server.add_handler(path="/health", handler=handlers.health, method=HTTPMethod.GET)
    grpc_server.add_interceptor(OpenTelemetryServerInterceptor())
    grpc_server.add_interceptor(ObservabilityServerInterceptor())
    producer.add_interceptor(ObservabilityProducerInterceptor())

    await service.run()


if __name__ == "__main__":
    container = Container()
    container.wire(packages=["."], modules=[__name__])
    asyncio.run(main())
