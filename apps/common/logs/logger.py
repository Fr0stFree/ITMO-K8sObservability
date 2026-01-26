import logging
import logging.config


def new_logger(config: dict, name: str) -> logging.Logger:
    logging.config.dictConfig(config)
    logger = logging.getLogger(name)
    return logger
