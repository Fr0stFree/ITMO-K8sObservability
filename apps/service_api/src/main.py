import asyncio

from service_api.src.container import Container
from service_api.src.service import APIService
from service_api.src.settings import APIServiceSettings


async def main() -> None:
    container = Container()
    container.settings.from_pydantic(APIServiceSettings())
    container.wire(packages=["."])
    service = APIService()
    await service.start()


if __name__ == "__main__":
    asyncio.run(main())
