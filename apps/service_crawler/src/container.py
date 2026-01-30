from dependency_injector import containers, providers

from common.brokers.kafka import KafkaProducer, KafkaProducerSettings
from common.databases.redis import RedisClient, RedisClientSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import new_logger, LoggingSettings
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_crawler.src.crawling import CrawlingPipeline
from service_crawler.src.rpc import RPCServicer


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name="crawler-service"))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)

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
    broker_producer = providers.Singleton(KafkaProducer, settings=KafkaProducerSettings(), logger=logger)
    db_client = providers.Singleton(RedisClient, settings=RedisClientSettings(), logger=logger)

    # domain
    crawling_pipeline = providers.Singleton(
        CrawlingPipeline,
        redis=db_client.provided.redis,
        concurrent_workers=settings.concurrent_workers,
        producer=broker_producer,
        logger=logger,
    )
