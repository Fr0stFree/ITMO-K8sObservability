from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from common.logs.logger import LoggerLike
from common.tracing.settings import TraceExporterSettings


class TraceExporter:
    def __init__(self, settings: TraceExporterSettings, logger: LoggerLike) -> None:
        self._settings = settings
        self._logger = logger

        self._provider: TracerProvider
        # self._exporter: OTLPSpanExporter

    async def start(self) -> None:
        if not self._settings.enabled:
            self._logger.info("Tracing is disabled")
            return

        self._logger.info(
            "Starting to exporting traces to '%s' utilizing '%s'",
            self._settings.otlp_endpoint,
            self._settings.protocol,
        )
        resource = Resource.create({"service.name": self._settings.service_name})
        # self._exporter = OTLPSpanExporter(endpoint=self._settings.otlp_endpoint, insecure=True)
        # self._exporter = ConsoleSpanExporter()

        self._provider = TracerProvider(resource=resource)

        # self._provider.add_span_processor(BatchSpanProcessor(self._exporter))
        self._provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(self._provider)

    async def stop(self) -> None:
        self._logger.info("Stopping trace exporter...")
        self._provider.shutdown()

    async def is_healthy(self) -> bool:
        if not self._settings.enabled:
            return True

        return True
