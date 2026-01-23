import datetime as dt

from pydantic_settings import BaseSettings

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


class MonitoringSettings(BaseSettings):
    grpc_workers: int = 10
    grpc_server_port: int = 50051
    http_server_port: int = 8000
    metrics_server_port: int = 9000
    health_check_timeout: dt.timedelta = dt.timedelta(seconds=2)
