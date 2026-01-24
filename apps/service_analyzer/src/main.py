import asyncio

from service_analyzer.src.container import Container
from service_analyzer.src.service import AnalyzerService
from service_analyzer.src.settings import AnalyzerServiceSettings


async def main() -> None:
    container = Container()
    container.settings.from_pydantic(AnalyzerServiceSettings())
    container.wire(packages=["."])
    service = AnalyzerService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
