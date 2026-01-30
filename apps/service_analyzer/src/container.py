from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaConsumer, KafkaConsumerSettings
from common.databases.postgres import PostgresClient, PostgresSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_analyzer.src.rpc import RPCServicer


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name="analyzer-service"))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)
    tracer = providers.Singleton(trace.get_tracer, "analyzer-service")

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
    broker_consumer = providers.Singleton(KafkaConsumer, settings=KafkaConsumerSettings(), logger=logger, tracer=tracer)

    # domain
    db_session = providers.Factory(db_client.provided.get_session)
