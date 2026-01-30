from dependency_injector.wiring import Provide, inject
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from service_analyzer.src.container import Container

tracer = trace.get_tracer(__name__)


@inject
async def on_new_message(
    message: dict,
    db_session: AsyncSession = Provide[Container.db_session],
    tracer=Provide[Container.tracer],
) -> None:
    with tracer.start_as_current_span("process_message"):
        print(f"GOT MESSAGE {message}")
