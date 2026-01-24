from pydantic import Field
from pydantic_settings import BaseSettings


class TraceExporterSettings(BaseSettings):
    service_name: str = Field("monitoring-service", alias="TRACE_EXPORTER_SERVICE_NAME")
    otlp_endpoint: str = Field("http://localhost:4317", alias="TRACE_EXPORTER_OTLP_ENDPOINT")
    protocol: str = Field("grpc", alias="TRACE_EXPORTER_PROTOCOL")
    enabled: bool = Field(True, alias="TRACE_EXPORTER_ENABLED")
