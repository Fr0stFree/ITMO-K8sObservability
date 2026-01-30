from dependency_injector import containers, providers

from common.grpc import GRPCClient
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
from protocol.crawler_pb2_grpc import CrawlerServiceStub


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name="api-service"))
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)

    # components
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    crawler_client = providers.Singleton(GRPCClient, address=settings.crawler_target_address, logger=logger)
    analyzer_client = providers.Singleton(GRPCClient, address=settings.analyzer_target_address, logger=logger)

    # domain
    crawler_stub = providers.Factory(CrawlerServiceStub, channel=crawler_client.provided.channel)
    analyzer_stub = providers.Factory(AnalyzerServiceStub, channel=analyzer_client.provided.channel)
