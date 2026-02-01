from dependency_injector.wiring import Provide, inject


from service_analyzer.src.container import Container


@inject
async def on_new_message(
    message: dict,
    tracer=Provide[Container.tracer],
) -> None:
    with tracer.start_as_current_span("process_message"):
        print(f"GOT MESSAGE {message}")
