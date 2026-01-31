from dependency_injector import containers, providers
from opentelemetry import trace
from prometheus_client import Counter, Histogram

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
    tracer = providers.Singleton(trace.get_tracer, "api-service")
    metrics_server = providers.Singleton(MetricsServer, settings=MetricsServerSettings(), logger=logger)
    trace_exporter = providers.Singleton(TraceExporter, settings=TraceExporterSettings(), logger=logger)

    # metrics
    requests_counter = providers.Singleton(
        Counter,
        "service_api_http_requests_total",
        "Total number of HTTP requests",
        ["method", "endpoint", "http_status"],
    )
    request_latency = providers.Singleton(
        Histogram,
        "service_api_http_request_latency_seconds",
        "Latency of HTTP requests in seconds",
        ["method", "endpoint"],
    )

    # components
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    crawler_client = providers.Singleton(GRPCClient, address=settings.crawler_target_address, logger=logger)
    analyzer_client = providers.Singleton(GRPCClient, address=settings.analyzer_target_address, logger=logger)

    # domain
    crawler_stub = providers.Factory(CrawlerServiceStub, channel=crawler_client.provided.channel)
    analyzer_stub = providers.Factory(AnalyzerServiceStub, channel=analyzer_client.provided.channel)
