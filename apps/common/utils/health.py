import asyncio
import datetime as dt

from common.types.interface import IHealthCheck


async def check_health(*components: IHealthCheck, timeout: dt.timedelta) -> dict[IHealthCheck, bool]:
    checks = {component: component.is_healthy() for component in components}
    results = await asyncio.wait_for(
        asyncio.gather(*checks.values(), return_exceptions=True),
        timeout=timeout.total_seconds(),
    )

    state = {}
    for component, result in zip(checks.keys(), results):
        is_alive = False if isinstance(result, Exception) else result
        state[component] = is_alive
    return state
