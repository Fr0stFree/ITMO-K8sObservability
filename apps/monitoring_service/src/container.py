from dependency_injector import containers, providers

from common.databases.postgres.client import PostgresClient
from common.databases.postgres.settings import PostgresSettings
from common.grpc.server import GRPCServer
from common.grpc.settings import GRPCServerSettings
from common.http.server import HTTPServer
from common.http.settings import HTTPServerSettings
from common.logs.logger import new_logger
from common.logs.settings import LOGGING_CONFIG
from common.metrics.server import MetricsServer
from common.metrics.settings import MetricsServerSettings
from common.tracing.exporter import TraceExporter
from common.tracing.settings import TraceExporterSettings
from monitoring_service.src.handlers.rpc import RPCServicer


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name="MonitoringService")
    http_server = providers.Singleton(
        HTTPServer,
        settings=HTTPServerSettings(),
        logger=logger,
    )
    metrics_server = providers.Singleton(
        MetricsServer,
        settings=MetricsServerSettings(),
        logger=logger,
    )
    rpc_servicer = providers.Singleton(RPCServicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        servicer=rpc_servicer,
        registerer=rpc_servicer.provided.registerer,
        settings=GRPCServerSettings(),
        logger=logger,
    )
    db_client = providers.Singleton(
        PostgresClient,
        settings=PostgresSettings(),
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        settings=TraceExporterSettings(),
        logger=logger,
    )
