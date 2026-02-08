import logging

from common.logs.filters import OpenTelemetryLogFilter
from common.logs.formatters import ConsoleFormatter
import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource


# TODO: implement lifecycle
def new_logger(
    name: str,
    exporter_endpoint: str = "http://localhost:4317", # TODO: make it configurable
    level: int = logging.INFO,
) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    console_formatter = ConsoleFormatter()
    otel_filter = OpenTelemetryLogFilter()

    # Console handler for human-readable logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(otel_filter)
    logger.addHandler(console_handler)

    # OTLP handler for structured logs
    logger_provider = LoggerProvider(resource=Resource.create({"service.name": name}))
    set_logger_provider(logger_provider)
    exporter = OTLPLogExporter(insecure=True, endpoint=exporter_endpoint)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logger.addHandler(handler)

    logger.propagate = False

    return logger
