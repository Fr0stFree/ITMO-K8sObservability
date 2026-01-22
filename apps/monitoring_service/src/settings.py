from pydantic_settings import BaseSettings
import logging
import logging.config


class MonitoringSettings(BaseSettings):
    rpc_workers: int = 10
    rpc_server_port: int = 50051
    metrics_server_port: int = 8000

    @property
    def logging(self) -> dict:
        return {
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
