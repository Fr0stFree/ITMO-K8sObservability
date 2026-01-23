from pydantic_settings import BaseSettings


class TraceExporterSettings(BaseSettings):
    service_name: str = "monitoring-service"
    otlp_endpoint: str = "http://localhost:4317"
    protocol: str = "grpc"
    enabled: bool = True
