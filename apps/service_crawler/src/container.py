from dependency_injector import containers, providers
from opentelemetry import trace
from prometheus_client import Counter, Histogram

from common.brokers.kafka import KafkaProducer, KafkaProducerSettings
from common.databases.redis import RedisClient, RedisClientSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.service.service import BaseService
from common.service.settings import ServiceSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_crawler.src.factories import new_crawling_pipeline, new_rpc_servicer
from service_crawler.src.settings import CrawlerServiceSettings


class Container(containers.DeclarativeContainer):
    service_name = "crawler-service"
    settings = providers.Configuration(pydantic_settings=[CrawlerServiceSettings()])

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name=service_name))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)
    tracer = providers.Singleton(trace.get_tracer, service_name)
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
        servicer=rpc_servicer,
        registerer=rpc_servicer.provided.registerer,
        settings=GRPCServerSettings(),
        logger=logger,
    )
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    broker_producer = providers.Singleton(KafkaProducer, settings=KafkaProducerSettings(), logger=logger, tracer=tracer)
    db_client = providers.Singleton(RedisClient, settings=RedisClientSettings(), logger=logger)
    crawling_pipeline = providers.Singleton(new_crawling_pipeline, concurrent_workers=settings.concurrent_workers)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            http_server,
            metrics_server,
            trace_exporter,
            grpc_server,
            db_client,
            broker_producer,
            # crawling_pipeline,
        ),
        settings=ServiceSettings(name=service_name),
        logger=logger,
    )
