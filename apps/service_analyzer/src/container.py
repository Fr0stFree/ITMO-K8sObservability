from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaConsumer
from common.databases.postgres import PostgresClient
from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import LoggerHandle
from common.metrics import MetricsExporter
from common.service import BaseService
from common.tracing import TraceExporter
from service_analyzer.src.factories import new_repository, new_rpc_servicer
from service_analyzer.src.settings import AnalyzerServiceSettings


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[AnalyzerServiceSettings()])

    # observability
    logger_handle = providers.Singleton(
        LoggerHandle,
        name=settings.service_name,
        is_export_enabled=settings.logging.is_export_enabled,
        exporting_endpoint=settings.logging.exporting_endpoint,
        level=settings.logging.level,
    )
    logger = logger_handle.provided.logger
    metrics_exporter = providers.Singleton(
        MetricsExporter,
        name=settings.service_name,
        endpoint=settings.metrics_exporter.otlp_endpoint,
        is_enabled=settings.metrics_exporter.enabled,
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        name=settings.service_name,
        endpoint=settings.trace_exporter.otlp_endpoint,
        is_enabled=settings.trace_exporter.enabled,
        logger=logger,
    )
    tracer = providers.Singleton(trace.get_tracer, settings.service_name)
    current_span = providers.Factory(trace.get_current_span)

    # metrics
    grpc_incoming_requests_counter = providers.Singleton(
        metrics_exporter.provided.meter.create_counter.call(),
        name="service_analyzer_incoming_grpc_requests_total",
        description="Total number of incoming gRPC requests",
        unit="1",
    )
    grpc_incoming_requests_latency = providers.Singleton(
        metrics_exporter.provided.meter.create_histogram.call(),
        name="service_analyzer_incoming_grpc_requests_latency_seconds",
        description="Latency of incoming gRPC requests in seconds",
        unit="s",
    )
    # TODO: consumer counter

    # components
    http_server = providers.Singleton(
        HTTPServer,
        port=settings.http_server.port,
        logger=logger,
    )
    rpc_servicer = providers.Singleton(new_rpc_servicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        worker_amount=settings.grpc_server.worker_amount,
        port=settings.grpc_server.port,
        logger=logger,
    )
    db_client = providers.Singleton(
        PostgresClient,
        user=settings.postgres.user,
        password=settings.postgres.password,
        host=settings.postgres.host,
        port=settings.postgres.port,
        database=settings.postgres.database,
        logger=logger,
    )
    broker_consumer = providers.Singleton(
        KafkaConsumer,
        topic=settings.kafka_consumer.topic,
        address=settings.kafka_consumer.address,
        client_prefix=settings.service_name,
        group_id=settings.kafka_consumer.group_id,
        logger=logger,
    )
    repository = providers.Singleton(new_repository)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            logger_handle,
            http_server,
            metrics_exporter,
            trace_exporter,
            grpc_server,
            db_client,
            repository,
            broker_consumer,
        ),
        name=settings.service_name,
        health_check_timeout=settings.health_check_timeout,
        logger=logger,
    )
