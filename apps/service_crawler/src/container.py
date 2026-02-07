from dependency_injector import containers, providers
from opentelemetry import trace
from prometheus_client import Counter, Histogram

from common.brokers.kafka import KafkaProducer
from common.databases.redis import RedisClient
from common.grpc import GRPCServer
from common.http import HTTPServer
from common.logs import new_logger
from common.metrics import MetricsServer
from common.service.service import BaseService
from common.tracing import TraceExporter
from service_crawler.src.factories import new_crawling_pipeline, new_repository, new_rpc_servicer
from service_crawler.src.settings import CrawlerServiceSettings


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[CrawlerServiceSettings()])

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

    # metrics
    crawled_urls_counter = providers.Singleton(
        Counter,
        "crawled_urls_total",
        "Total number of crawled URLs",
        ["status"],
    )
    rpc_request_latency = providers.Singleton(
        Histogram,
        "service_crawler_grpc_request_latency_seconds",
        "Latency of gRPC requests in seconds",
        ["method"],
    )

    # components
    rpc_servicer = providers.Singleton(new_rpc_servicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        worker_amount=settings.grpc_server.worker_amount,
        port=settings.grpc_server.port,
        logger=logger,
    )
    http_server = providers.Singleton(
        HTTPServer,
        port=settings.http_server.port,
        logger=logger,
    )
    broker_producer = providers.Singleton(
        KafkaProducer,
        topic=settings.kafka_producer.topic,
        address=settings.kafka_producer.address,
        client_prefix=settings.service_name,
        logger=logger,
    )
    db_client = providers.Singleton(
        RedisClient,
        host=settings.redis.host,
        port=settings.redis.port,
        password=settings.redis.password,
        database=settings.redis.database,
        logger=logger,
    )
    crawling_pipeline = providers.Singleton(new_crawling_pipeline, concurrent_workers=settings.concurrent_workers)
    repository = providers.Singleton(new_repository)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            http_server,
            metrics_server,
            trace_exporter,
            grpc_server,
            db_client,
            broker_producer,
            crawling_pipeline,
            repository,
        ),
        name=settings.service_name,
        health_check_timeout=settings.health_check_timeout,
        logger=logger,
    )
