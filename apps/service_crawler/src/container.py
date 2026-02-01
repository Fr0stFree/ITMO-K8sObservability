from dependency_injector import containers, providers
from opentelemetry import trace

from common.brokers.kafka import KafkaProducer, KafkaProducerSettings
from common.databases.redis import RedisClient, RedisClientSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.service.service import BaseService
from common.service.settings import ServiceSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_crawler.src.factories import new_crawling_pipeline
from service_crawler.src.grpc.servicer import RPCServicer


class Container(containers.DeclarativeContainer):
    service_name = "crawler-service"
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name=service_name))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)
    tracer = providers.Singleton(trace.get_tracer, service_name)

    # components
    rpc_servicer = providers.Singleton(RPCServicer)
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

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            http_server,
            metrics_server,
            trace_exporter,
            grpc_server,
            db_client,
            broker_producer,
        ),
        settings=ServiceSettings(name=service_name),
        logger=logger,
    )

    # domain
    crawling_pipeline = providers.Singleton(new_crawling_pipeline, concurrent_workers=settings.concurrent_workers)
