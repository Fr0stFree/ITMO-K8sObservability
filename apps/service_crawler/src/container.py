import asyncio

from dependency_injector import containers, providers

from common.grpc import GRPCServer, GRPCServerSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import new_logger
from common.logs.settings import LOGGING_CONFIG
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from service_crawler.src.rpc import RPCServicer
from service_crawler.src.url_crawler import CrawlerPool
from service_crawler.src.url_dumper import URLDumper


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name=settings.service_name)
    http_server = providers.Singleton(
        HTTPServer,
        settings=HTTPServerSettings(),
        logger=logger,
    )
    metrics_server = providers.Singleton(
        MetricsServer,
        settings=MetricsServerSettings(),
        logger=logger,
    )
    rpc_servicer = providers.Singleton(RPCServicer)
    grpc_server = providers.Singleton(
        GRPCServer,
        servicer=rpc_servicer,
        registerer=rpc_servicer.provided.registerer,
        settings=GRPCServerSettings(),
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        settings=TraceExporterSettings(),
        logger=logger,
    )
    urls_queue = providers.Singleton(asyncio.Queue, maxsize=100)
    crawler_pool = providers.Singleton(
        CrawlerPool,
        queue=urls_queue,
        urls=["http://wikipedia.org", "http://example.com", "http://nonexistent.baddomain"],
        amount=settings.concurrent_crawlers,
        logger=logger,
    )
    dumper = providers.Singleton(URLDumper, queue=urls_queue, logger=logger)
