import asyncio

from monitoring_service.src.container import Container
from monitoring_service.src.service import MonitoringService
from monitoring_service.src.settings import MonitoringServiceSettings


async def main() -> None:
    container = Container()
    container.settings.from_pydantic(MonitoringServiceSettings())
    container.wire(packages=["."])
    service = MonitoringService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
