from dependency_injector import containers, providers
from opentelemetry import trace
from prometheus_client import Counter, Histogram

from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerHandle
from common.metrics import MetricsServer
from common.service.service import BaseService
from common.tracing import TraceExporter
from protocol.analyzer_pb2_grpc import AnalyzerServiceStub
from protocol.crawler_pb2_grpc import CrawlerServiceStub
from service_api.src.settings import APIServiceSettings


class Container(containers.DeclarativeContainer):
    settings = providers.Configuration(pydantic_settings=[APIServiceSettings()])

    # observability
    logger_handle = providers.Singleton(
        LoggerHandle,
        name=settings.service_name,
        is_export_enabled=settings.logging.is_export_enabled,
        exporting_endpoint=settings.logging.exporting_endpoint,
        level=settings.logging.level,
    )
    logger = logger_handle.provided.logger
    tracer = providers.Singleton(trace.get_tracer, settings.service_name)
    current_span = providers.Factory(trace.get_current_span)
    metrics_server = providers.Singleton(
        MetricsServer,
        port=settings.metrics_server.port,
        logger=logger,
    )
    trace_exporter = providers.Singleton(
        TraceExporter,
        name=settings.service_name,
        endpoint=settings.trace_exporter.otlp_endpoint,
        is_enabled=settings.trace_exporter.enabled,
        logger=logger,
    )

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
    rpc_request_counter = providers.Singleton(
        Counter,
        "service_api_grpc_requests_total",
        "Total number of gRPC requests",
        ["method"],
    )
    rpc_request_latency = providers.Singleton(
        Histogram,
        "service_api_grpc_request_latency_seconds",
        "Latency of gRPC requests in seconds",
        ["method"],
    )

    # components
    http_server = providers.Singleton(HTTPServer, port=settings.http_server.port, logger=logger)
    crawler_client = providers.Singleton(
        GRPCClient, address=settings.crawler_client.address, logger=logger, stub_class=CrawlerServiceStub
    )
    analyzer_client = providers.Singleton(
        GRPCClient, address=settings.analyzer_client.address, logger=logger, stub_class=AnalyzerServiceStub
    )

    service = providers.Singleton(
        BaseService,
        components=providers.List(
            logger_handle,
            http_server,
            metrics_server,
            trace_exporter,
        ),
        health_check_timeout=settings.health_check_timeout,
        name=settings.service_name,
        logger=logger,
    )
