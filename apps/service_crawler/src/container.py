from dependency_injector import containers, providers

from common.brokers.kafka import KafkaProducer, KafkaProducerSettings
from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import new_logger
from common.logs.settings import LOGGING_CONFIG
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_crawler.src.crawling.pipeline import CrawlingPipeline
from service_crawler.src.rpc import RPCServicer


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name=settings.service_name)
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

    # domain
    crawling_pipeline = providers.Singleton(
        CrawlingPipeline,
        urls=["http://wikipedia.org", "http://example.com", "http://nonexistent.baddomain"],
        concurrent_workers=settings.concurrent_workers,
        producer=broker_producer,
        logger=logger,
    )
