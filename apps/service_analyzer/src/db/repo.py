from collections.abc import Callable

from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select

from service_analyzer.src.container import Container
from service_analyzer.src.db.schema import Base, TargetCheckDB, TargetDB
from service_analyzer.src.models import TargetDetails, TargetHistoryItem, TargetSummary, TargetUpdate


class Repository:
    @inject
    async def start(self, engine: AsyncEngine = Provide[Container.db_client.provided.engine]) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @inject
    async def stop(self, engine: AsyncEngine = Provide[Container.db_client.provided.engine]) -> None:
        pass
        # async with engine.begin() as conn:
        #     await conn.run_sync(Base.metadata.drop_all)

    async def is_healthy(self) -> bool:
        return True

    @inject
    async def update_target(
        self,
        payload: TargetUpdate,
        sessionmaker: Callable[[], AsyncSession] = Provide[Container.db_client.provided.sessionmaker],
    ) -> None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.url == payload.url))
            target = result.scalar_one_or_none()
            if not target:
                target = TargetDB(url=payload.url)
                session.add(target)
                await session.flush()

            target_check = TargetCheckDB(target_id=target.id, status=payload.status, comment=payload.comment)
            session.add(target_check)
            await session.commit()

    @inject
    async def get_target(
        self,
        id: str,
        sessionmaker: Callable[[], AsyncSession] = Provide[Container.db_client.provided.sessionmaker],
    ) -> TargetDetails | None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.id == id))
            target = result.scalar_one_or_none()
            if not target:
                return None

            result = await session.execute(
                select(TargetCheckDB.status, TargetCheckDB.checked_at, TargetCheckDB.comment)
                .where(TargetCheckDB.target_id == target.id)
                .order_by(TargetCheckDB.checked_at.desc())
            )
            checks = result.all()

            history = [
                TargetHistoryItem(status=check.status, checked_at=check.checked_at, comment=check.comment)
                for check in checks
            ]
            return TargetDetails(id=str(target.id), url=target.url, created_at=target.created_at, history=history)

    @inject
    async def list_targets(
        self,
        limit: int,
        offset: int,
        sessionmaker: Callable[[], AsyncSession] = Provide[Container.db_client.provided.sessionmaker],
    ) -> list[TargetSummary]:
        async with sessionmaker() as session:
            subquery = (
                select(TargetCheckDB.target_id, TargetCheckDB.status, TargetCheckDB.checked_at, TargetCheckDB.comment)
                .distinct(TargetCheckDB.target_id)
                .order_by(TargetCheckDB.target_id, TargetCheckDB.checked_at.desc())
                .subquery()
            )
            statement = (
                select(
                    TargetDB.id,
                    TargetDB.url,
                    subquery.c.status,
                    subquery.c.checked_at,
                    subquery.c.comment,
                    TargetDB.created_at,
                )
                .join(subquery, subquery.c.target_id == TargetDB.id)
                .order_by(subquery.c.checked_at.desc())
                .limit(limit)
                .offset(offset)
            )
            results = await session.execute(statement)
            return [
                TargetSummary(
                    id=str(result.id),
                    url=result.url,
                    status=result.status,
                    checked_at=result.checked_at,
                    comment=result.comment,
                    created_at=result.created_at,
                )
                for result in results.all()
            ]

    @inject
    async def delete_target(
        self,
        id: str,
        sessionmaker: Callable[[], AsyncSession] = Provide[Container.db_client.provided.sessionmaker],
    ) -> None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.id == id))
            target = result.scalar_one_or_none()
            if target:
                await session.delete(target)
                await session.commit()
