from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.metrics import set_meter_provider, Meter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from common.logs.interface import LoggerLike
from opentelemetry.sdk.resources import Resource

from common.logs.interface import LoggerLike


class MetricsExporter:
    def __init__(self, name: str, endpoint: str, logger: LoggerLike) -> None:
        self._name = name
        self._endpoint = endpoint
        self._logger = logger

        self._exporter: OTLPMetricExporter
        self._reader: PeriodicExportingMetricReader
        self._provider: MeterProvider

    async def start(self) -> None:
        resource = Resource.create({"service.name": self._name})
        self._exporter = OTLPMetricExporter(endpoint=self._endpoint, insecure=True)
        self._reader = PeriodicExportingMetricReader(self._exporter, export_interval_millis=5000)
        self._provider = MeterProvider(resource=resource, metric_readers=[self._reader])
        set_meter_provider(self._provider)
        self._logger.info("Metrics exporter is enabled to '%s'", self._endpoint)

    async def stop(self) -> None:
        self._logger.info("Stopping metrics exporter...")
        self._reader.shutdown()
        self._exporter.shutdown()

    async def is_healthy(self) -> bool:
        return True

    @property
    def meter(self) -> Meter:
        return self._provider.get_meter(self._name)
