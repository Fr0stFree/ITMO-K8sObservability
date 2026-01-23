import logging
import logging.config

type LoggerLike = logging.Logger | logging.LoggerAdapter


def new_logger(config: dict, name: str) -> logging.Logger:
    logging.config.dictConfig(config)
    logger = logging.getLogger(name)
    return logger
