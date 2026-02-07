import datetime as dt
import logging

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class MetricsServerSettings(BaseModel):
    port: int = Field(..., alias="PORT")


class TraceExporterSettings(BaseModel):
    otlp_endpoint: str = Field(..., alias="OTLP_ENDPOINT")
    protocol: str = Field("grpc", alias="PROTOCOL")
    enabled: bool = Field(True, alias="IS_ENABLED")


class LoggingSettings(BaseModel):
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", alias="FORMAT")
    level: int = Field(logging.INFO, alias="LEVEL")
    file_path: str = Field(..., alias="FILE_PATH")
    file_max_bytes: int = Field(10 * 1024 * 1024, alias="FILE_MAX_BYTES")
    file_backup_count: int = Field(2, alias="FILE_BACKUP_COUNT")


class HTTPServerSettings(BaseModel):
    port: int = Field(..., alias="PORT")


class AnalyzerClientSettings(BaseModel):
    address: str = Field(..., alias="ADDRESS")


class CrawlerClientSettings(BaseModel):
    address: str = Field(..., alias="ADDRESS")


class APIServiceSettings(BaseSettings):
    service_name: str = Field("api-service", alias="SERVICE_NAME")
    pagination_default_limit: int = Field(50, alias="PAGINATION_DEFAULT_LIMIT")
    pagination_max_limit: int = Field(100, alias="PAGINATION_MAX_LIMIT")
    health_check_timeout: dt.timedelta = Field(dt.timedelta(seconds=5), alias="HEALTH_CHECK_TIMEOUT")

    logging: LoggingSettings
    metrics_server: MetricsServerSettings
    trace_exporter: TraceExporterSettings
    http_server: HTTPServerSettings
    analyzer_client: AnalyzerClientSettings
    crawler_client: CrawlerClientSettings

    model_config = ConfigDict(env_nested_delimiter="__")
