from common.types.interface import ILifeCycle, IHealthCheck
from common.service.settings import ServiceSettings


class IService(IHealthCheck):
    async def run(self) -> None: ...

class IServiceComponent(ILifeCycle, IHealthCheck):
    pass