import logging
import logging.handlers
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from common.logs.filters import OpenTelemetryLogFilter
from common.logs.formatters import ConsoleFormatter


def new_logger(
    name: str,
    format: str,
    file_path: Path,
    level: int = logging.INFO,
    file_max_bytes: int = 10 * 1024 * 1024,
    file_backup_count: int = 2,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    json_formatter = JsonFormatter(format)
    console_formatter = ConsoleFormatter()
    otel_filter = OpenTelemetryLogFilter()

    # Console handler for human-readable logs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(otel_filter)
    logger.addHandler(console_handler)

    # Rotating file handler for structured logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=file_path,
        maxBytes=file_max_bytes,
        backupCount=file_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(otel_filter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger
