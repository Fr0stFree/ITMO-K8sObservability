import datetime as dt
import logging

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class MetricsServerSettings(BaseModel):
    port: int = Field(..., alias="PORT")


class TraceExporterSettings(BaseModel):
    otlp_endpoint: str = Field(..., alias="OTLP_ENDPOINT")
    enabled: bool = Field(True, alias="IS_ENABLED")


class LoggingSettings(BaseModel):
    is_export_enabled: bool = Field(False, alias="IS_EXPORT_ENABLED")
    exporting_endpoint: str | None = Field(None, alias="EXPORTING_ENDPOINT")
    level: int = Field(logging.INFO, alias="LEVEL")


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
