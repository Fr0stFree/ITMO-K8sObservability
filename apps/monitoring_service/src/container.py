from dependency_injector import containers, providers

from common.grpc.server import GRPCServer
from common.http.server import HTTPServer
from common.logs.logger import new_logger
from common.metrics.server import MetricsServer
from monitoring_service.src.rpc import RPCServicer
from monitoring_service.src.settings import LOGGING_CONFIG


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name="MonitoringService")
    http_server = providers.Singleton(
        HTTPServer,
        port=config.http_server_port,
        logger=logger,
    )
    metrics_server = providers.Singleton(
        MetricsServer,
        port=config.metrics_server_port,
        logger=logger,
    )
    rpc_servicer = providers.Singleton(RPCServicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        servicer=rpc_servicer,
        registerer=rpc_servicer.provided.registerer,
        workers=config.grpc_workers,
        port=config.grpc_server_port,
        logger=logger,
    )
