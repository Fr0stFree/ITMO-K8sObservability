from dependency_injector import containers, providers

from common.brokers.kafka import KafkaConsumer, KafkaConsumerSettings
from common.databases.postgres import PostgresClient, PostgresSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import new_logger
from common.logs.settings import LOGGING_CONFIG
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_analyzer.src.rpc import RPCServicer


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name=settings.service_name)
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)

    # components
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    rpc_servicer = providers.Singleton(RPCServicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        servicer=rpc_servicer,
        registerer=rpc_servicer.provided.registerer,
        settings=GRPCServerSettings(),
        logger=logger,
    )
    db_client = providers.Singleton(PostgresClient, settings=PostgresSettings(), logger=logger)
    broker_consumer = providers.Singleton(KafkaConsumer, settings=KafkaConsumerSettings(), logger=logger)
