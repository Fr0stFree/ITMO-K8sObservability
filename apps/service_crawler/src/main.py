import asyncio

from service_crawler.src.container import Container
from service_crawler.src.service import MonitoringService
from service_crawler.src.settings import MonitoringServiceSettings


async def main() -> None:
    container = Container()
    container.settings.from_pydantic(MonitoringServiceSettings())
    container.wire(packages=["."])
    service = MonitoringService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
