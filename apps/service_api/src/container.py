from dependency_injector import containers, providers

from common.grpc import GRPCClient, GRPCClientSettings
from common.http import HTTPServer, HTTPServerSettings
from common.logs import new_logger
from common.logs.settings import LOGGING_CONFIG
from common.metrics import MetricsServer, MetricsServerSettings
from common.tracing import TraceExporter, TraceExporterSettings
from protocol.crawler_pb2_grpc import CrawlerServiceStub


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration()

    logger = providers.Singleton(new_logger, config=LOGGING_CONFIG, name="APIService")
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)
    crawler_client = providers.Singleton(GRPCClient, settings=GRPCClientSettings(), logger=logger)
    crawler_stub = providers.Factory(CrawlerServiceStub, channel=crawler_client.provided.channel)
