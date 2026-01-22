import asyncio

from monitoring_service.src.service import MonitoringService
from monitoring_service.src.settings import MonitoringSettings


async def main() -> None:
    settings = MonitoringSettings()
    service = MonitoringService(settings)
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
