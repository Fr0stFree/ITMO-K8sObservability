from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaConsumer, KafkaConsumerSettings
from common.databases.postgres import PostgresClient, PostgresSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.service import BaseService, ServiceSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_analyzer.src.factories import new_repository, new_rpc_servicer
from service_analyzer.src.settings import AnalyzerServiceSettings


class Container(containers.DeclarativeContainer):
    service_name = "analyzer-service"
    settings = providers.Configuration(pydantic_settings=[AnalyzerServiceSettings()])

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name=service_name))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)
    tracer = providers.Singleton(trace.get_tracer, service_name)
    current_span = providers.Factory(trace.get_current_span)

    # components
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    rpc_servicer = providers.Singleton(new_rpc_servicer)
    grpc_server = providers.Singleton(GRPCServer, settings=GRPCServerSettings(), logger=logger)
    db_client = providers.Singleton(PostgresClient, settings=PostgresSettings(), logger=logger)
    broker_consumer = providers.Singleton(KafkaConsumer, settings=KafkaConsumerSettings(), logger=logger, tracer=tracer)
    repository = providers.Singleton(new_repository)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            http_server,
            metrics_server,
            trace_exporter,
            grpc_server,
            db_client,
            repository,
            broker_consumer,
        ),
        settings=ServiceSettings(name=service_name),
        logger=logger,
    )
