from common.types.interface import IHealthCheck, ILifeCycle


class IService(IHealthCheck):
    async def run(self) -> None: ...


class IServiceComponent(ILifeCycle, IHealthCheck):
    pass
