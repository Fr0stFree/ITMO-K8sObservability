from pydantic_settings import BaseSettings


class MonitoringSettings(BaseSettings):
    grpc_workers: int = 10
    grpc_server_port: int = 50051
    http_server_port: int = 8000
    metrics_server_port: int = 9000

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
