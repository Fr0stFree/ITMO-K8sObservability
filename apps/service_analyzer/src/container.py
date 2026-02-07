from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaConsumer
from common.databases.postgres import PostgresClient
from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import new_logger
from common.metrics import MetricsServer
from common.service import BaseService
from common.tracing import TraceExporter
from service_analyzer.src.factories import new_repository, new_rpc_servicer
from service_analyzer.src.settings import AnalyzerServiceSettings


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[AnalyzerServiceSettings()])

    # observability
    logger = providers.Singleton(
        new_logger,
        name=settings.service_name,
        format=settings.logging.format,
        file_path=settings.logging.file_path,
        level=settings.logging.level,
        file_max_bytes=settings.logging.file_max_bytes,
        file_backup_count=settings.logging.file_backup_count,
    )
    metrics_server = providers.Singleton(
        MetricsServer,
        port=settings.metrics_server.port,
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        name=settings.service_name,
        endpoint=settings.trace_exporter.otlp_endpoint,
        protocol=settings.trace_exporter.protocol,
        is_enabled=settings.trace_exporter.enabled,
        logger=logger,
    )
    tracer = providers.Singleton(trace.get_tracer, settings.service_name)
    current_span = providers.Factory(trace.get_current_span)

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
            http_server,
            metrics_server,
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
