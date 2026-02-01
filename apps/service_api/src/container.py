from re import A
from dependency_injector import containers, providers
from opentelemetry import trace
from prometheus_client import Counter, Histogram

from common.grpc import GRPCClient
from common.http import HTTPServer, HTTPServerSettings
from common.logs import LoggingSettings, new_logger
from common.metrics import MetricsServer, MetricsServerSettings
from common.service.service import BaseService
from common.service.settings import ServiceSettings
from common.tracing import TraceExporter, TraceExporterSettings
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
from protocol.crawler_pb2_grpc import CrawlerServiceStub
from service_api.src.settings import APIServiceSettings


class Container(containers.DeclarativeContainer):
    service_name = "api-service"
    settings = providers.Configuration(pydantic_settings=[APIServiceSettings()])

    # observability
    logger = providers.Singleton(new_logger, settings=LoggingSettings(name=service_name))
    tracer = providers.Singleton(trace.get_tracer, service_name)
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
    rpc_request_latency = providers.Singleton(
        Histogram,
        "service_api_grpc_request_latency_seconds",
        "Latency of gRPC requests in seconds",
        ["method"],
    )


    # components
    http_server = providers.Singleton(HTTPServer, settings=HTTPServerSettings(), logger=logger)
    crawler_client = providers.Singleton(GRPCClient, address=settings.crawler_target_address, logger=logger)
    analyzer_client = providers.Singleton(GRPCClient, address=settings.analyzer_target_address, logger=logger)

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            http_server,
            metrics_server,
            trace_exporter,
            crawler_client,
            analyzer_client,
        ),
        settings=ServiceSettings(name=service_name),
        logger=logger,
    )

    # domain
    crawler_stub = providers.Factory(CrawlerServiceStub, channel=crawler_client.provided.channel)
    analyzer_stub = providers.Factory(AnalyzerServiceStub, channel=analyzer_client.provided.channel)
