import logging

from pythonjsonlogger.json import JsonFormatter

from common.logs.filters import OpenTelemetryLogFilter
from common.logs.settings import LoggingSettings


def new_logger(settings: LoggingSettings) -> logging.Logger:
    logger = logging.getLogger(settings.name)
    logger.setLevel(settings.level)
    logger.handlers.clear()

    formatter = JsonFormatter(settings.format)
    filter = OpenTelemetryLogFilter()

    handler = logging.StreamHandler()
    handler.setLevel(settings.level)
    handler.setFormatter(formatter)
    handler.addFilter(filter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger
