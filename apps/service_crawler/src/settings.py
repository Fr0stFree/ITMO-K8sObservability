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


class GRPCServerSettings(BaseModel):
    port: int = Field(..., alias="PORT")
    worker_amount: int = Field(10, alias="WORKER_AMOUNT")


class RedisClientSettings(BaseModel):
    host: str = Field(..., alias="HOST")
    port: int = Field(..., alias="PORT")
    password: str = Field(..., alias="PASSWORD")
    database: str = Field(..., alias="DATABASE")


class KafkaProducerSettings(BaseModel):
    address: str = Field(..., alias="BOOTSTRAP_SERVERS")
    topic: str = Field(..., alias="TOPIC")


class CrawlerServiceSettings(BaseSettings):
    service_name: str = Field("crawler-service", alias="SERVICE_NAME")
    concurrent_workers: int = Field(
        default=1,
        ge=0,
        le=100,
        alias="CRAWLER_CONCURRENT_WORKERS",
    )
    worker_request_timeout: dt.timedelta = Field(
        default=dt.timedelta(seconds=10),
        alias="CRAWLER_WORKER_REQUEST_TIMEOUT",
    )
    health_check_timeout: dt.timedelta = Field(
        default=dt.timedelta(seconds=2),
        alias="CRAWLER_HEALTH_CHECK_TIMEOUT",
    )

    logging: LoggingSettings
    metrics_server: MetricsServerSettings
    trace_exporter: TraceExporterSettings
    http_server: HTTPServerSettings
    grpc_server: GRPCServerSettings
    redis: RedisClientSettings
    kafka_producer: KafkaProducerSettings

    model_config = ConfigDict(env_nested_delimiter="__")
