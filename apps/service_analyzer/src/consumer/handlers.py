from dependency_injector.wiring import Provide, inject
from opentelemetry.trace import Tracer

from common.logs.interface import LoggerLike
from service_analyzer.src.container import Container
from service_analyzer.src.db.repo import Repository
from service_analyzer.src.models import TargetUpdate


@inject
async def on_new_message(
    message: dict,
    repo: Repository = Provide[Container.repository],
    tracer: Tracer = Provide[Container.tracer],
    logger: LoggerLike = Provide[Container.logger],
) -> None:
    with tracer.start_as_current_span("consumer.process_message"):
        target = TargetUpdate(
            url=message["url"],
            status=message["status"],
            checked_at=message["updated_at"],
            comment=message.get("comment") or "",
        )
        await repo.update_target(target)

    logger.info("Processed target url '%s'", message["url"], extra={"target.url": target.url})
