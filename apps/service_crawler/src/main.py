import asyncio

from service_crawler.src.container import Container
from service_crawler.src.service import CrawlerService
from service_crawler.src.settings import CrawlerServiceSettings


async def main() -> None:
    container = Container()
    container.settings.from_pydantic(CrawlerServiceSettings())
    container.wire(packages=["."])
    service = CrawlerService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
