from dependency_injector.wiring import Provide, inject
from opentelemetry import trace
from opentelemetry.propagate import extract as extract_trace
from sqlalchemy.ext.asyncio import AsyncSession

from service_analyzer.src.container import Container



tracer = trace.get_tracer(__name__)


@inject
async def on_new_message(message: dict, db_session: AsyncSession = Provide[Container.db_session]) -> None:
    print(f"GOT MESSAGE {message}")
    context = extract_trace(message["context"])
    print(f"{context = }")
