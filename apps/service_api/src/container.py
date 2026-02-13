from dependency_injector import containers, providers
from opentelemetry import trace

from common.grpc import GRPCClient
from common.http import HTTPServer
from common.logs import LoggerHandle
from common.metrics import MetricsExporter
from common.service import BaseService
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
    metrics_exporter = providers.Singleton(
        MetricsExporter,
        name=settings.service_name,
        endpoint=settings.metrics_exporter.otlp_endpoint,
        is_enabled=settings.metrics_exporter.enabled,
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
    http_incoming_requests_counter = providers.Singleton(
        metrics_exporter.provided.meter.create_counter.call(),
        name="service_api_incoming_http_requests_total",
        description="Total number of incoming HTTP requests",
        unit="1",
    )
    http_incoming_requests_latency = providers.Singleton(
        metrics_exporter.provided.meter.create_histogram.call(),
        name="service_api_incoming_http_requests_latency_seconds",
        description="Latency of incoming HTTP requests in seconds",
        unit="s",
    )
    grpc_outgoing_requests_counter = providers.Singleton(
        metrics_exporter.provided.meter.create_counter.call(),
        name="service_api_outgoing_grpc_requests_total",
        description="Total number of outgoing gRPC requests",
        unit="1",
    )
    grpc_outgoing_requests_latency = providers.Singleton(
        metrics_exporter.provided.meter.create_histogram.call(),
        name="service_api_outgoing_grpc_requests_latency_seconds",
        description="Latency of outgoing gRPC requests in seconds",
        unit="s",
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
            trace_exporter,
            metrics_exporter,
        ),
        health_check_timeout=settings.health_check_timeout,
        name=settings.service_name,
        logger=logger,
    )
