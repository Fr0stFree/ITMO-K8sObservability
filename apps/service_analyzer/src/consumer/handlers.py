import datetime as dt

from dependency_injector.wiring import Provide, inject
from opentelemetry.trace import Tracer

from common.logs.interface import LoggerLike
from service_analyzer.src.container import Container
from service_analyzer.src.db.repo import AnalyzerRepository


@inject
async def on_new_message(
    message: dict,
    repo: AnalyzerRepository = Provide[Container.repo],
    tracer: Tracer = Provide[Container.tracer],
    logger: LoggerLike = Provide[Container.logger],
) -> None:
    with tracer.start_as_current_span("consumer.process_message"):
        await repo.upsert_target(
            status=message["status"],
            url=message["url"],
            checked_at=dt.datetime.fromisoformat(message["updated_at"]),
            comment=message.get("comment", ""),
        )
        logger.info(f"Processed message for URL: {message['url']}")
