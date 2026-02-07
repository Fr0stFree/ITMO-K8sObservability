from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from common.logs import LoggerLike


class TraceExporter:
    def __init__(self, name: str, endpoint: str, protocol: str, is_enabled: bool, logger: LoggerLike) -> None:
        self._name = name
        self._endpoint = endpoint
        self._protocol = protocol
        self._is_enabled = is_enabled
        self._logger = logger

        self._provider: TracerProvider
        # self._exporter: OTLPSpanExporter

    async def start(self) -> None:
        if not self._is_enabled:
            self._logger.info("Tracing is disabled")
            return

        self._logger.info(
            "Starting to export traces to '%s' utilizing '%s'",
            self._endpoint,
            self._protocol,
        )
        resource = Resource.create({"service.name": self._name})
        # self._exporter = OTLPSpanExporter(endpoint=self._endpoint, insecure=True)
        # self._exporter = ConsoleSpanExporter()

        self._provider = TracerProvider(resource=resource)

        # self._provider.add_span_processor(BatchSpanProcessor(self._exporter))
        # self._provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(self._provider)

    async def stop(self) -> None:
        self._logger.info("Stopping trace exporter...")
        self._provider.shutdown()

    async def is_healthy(self) -> bool:
        if not self._is_enabled:
            return True

        return True
