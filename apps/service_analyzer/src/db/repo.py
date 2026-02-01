import datetime as dt

from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from service_analyzer.src.container import Container
from service_analyzer.src.db.models import Base, Target, TargetStatus


class AnalyzerRepository:

    @inject
    async def start(self, engine: AsyncEngine = Provide[Container.db_client.provided.engine]) -> None:
        async with engine.begin() as conn:
            print("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)

    @inject
    async def stop(self, engine: AsyncEngine = Provide[Container.db_client.provided.engine]) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def is_healthy(self) -> bool:
        return True

    @inject
    async def upsert_target(
        self,
        status: str,
        url: str,
        checked_at: dt.datetime,
        comment: str,
        sessionmaker: sessionmaker = Provide[Container.db_client.provided.sessionmaker],
    ) -> None:
        async with sessionmaker() as session:
            result = await session.execute(select(Target).where(Target.url == url))
            target = result.scalar_one_or_none()
            if not target:
                target = Target(url=url)
                session.add(target)
                await session.flush()

            target_status = TargetStatus(target_id=target.id, status=status, checked_at=checked_at, comments=comment)
            session.add(target_status)
            await session.commit()

