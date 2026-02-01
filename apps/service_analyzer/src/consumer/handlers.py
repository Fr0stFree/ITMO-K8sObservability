from dependency_injector.wiring import Provide, inject

from common.logs.interface import LoggerLike
from service_analyzer.src.container import Container


@inject
async def on_new_message(
    message: dict,
    tracer: Tracer = Provide[Container.tracer],
    logger: LoggerLike = Provide[Container.logger],
) -> None:
    with tracer.start_as_current_span("consumer.process_message"):
        logger.info(f"Processing new message: {message}")
