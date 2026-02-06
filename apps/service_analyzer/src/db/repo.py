from dependency_injector.wiring import Provide, inject
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.future import select
from sqlalchemy.orm import aliased, sessionmaker

from service_analyzer.src.container import Container
from service_analyzer.src.db.schema import Base, TargetDB, TargetStatusDB
from service_analyzer.src.models import Target, TargetUpdate


class Repository:
    @inject
    async def start(self, engine: AsyncEngine = Provide[Container.db_client.provided.engine]) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @inject
    async def stop(self) -> None:
        pass

    async def is_healthy(self) -> bool:
        return True

    @inject
    async def update_target(
        self,
        payload: TargetUpdate,
        sessionmaker: sessionmaker = Provide[Container.db_client.provided.sessionmaker],
    ) -> None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.url == payload.url))
            obj = result.scalar_one_or_none()
            if not obj:
                obj = TargetDB(url=payload.url)
                session.add(obj)
                await session.flush()

            target_status = TargetStatusDB(
                target_id=obj.id,
                status=payload.status,
                checked_at=payload.checked_at,
                comments=payload.comment,
            )
            session.add(target_status)
            await session.commit()

    @inject
    async def get_target(
        self,
        id: str,
        sessionmaker: sessionmaker = Provide[Container.db_client.provided.sessionmaker],
    ) -> Target | None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.id == id))
            target = result.scalar_one_or_none()
            if not target:
                return None

            result = await session.execute(
                select(TargetStatusDB)
                .where(TargetStatusDB.target_id == target.id)
                .order_by(TargetStatusDB.checked_at.desc())
            )
            target_status = result.scalar_one_or_none()
            if not target_status:
                return None

            return Target(
                id=str(target.id),
                url=target.url,
                status=target_status.status,
                checked_at=target_status.checked_at,
                comment=target_status.comments,
            )

    @inject
    async def list_targets(
        self,
        limit: int,
        offset: int,
        sessionmaker: sessionmaker = Provide[Container.db_client.provided.sessionmaker],
    ) -> list[Target]:
        async with sessionmaker() as session:
            subquery = (
                select(
                    TargetStatusDB.target_id,
                    func.max(TargetStatusDB.checked_at).label("max_checked_at"),
                )
                .group_by(TargetStatusDB.target_id)
                .subquery()
            )
            ts = aliased(TargetStatusDB)
            statement = (
                select(TargetDB, ts)
                .join(subquery, TargetDB.id == subquery.c.target_id)
                .join(ts, (ts.target_id == subquery.c.target_id) & (ts.checked_at == subquery.c.max_checked_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(statement)
            rows = result.all()
            targets = []
            for target_obj, status_obj in rows:
                targets.append(
                    Target(
                        id=str(target_obj.id),
                        url=target_obj.url,
                        status=status_obj.status,
                        checked_at=status_obj.checked_at,
                        comment=status_obj.comments,
                    )
                )
            return targets

    @inject
    async def delete_target(
        self,
        id: str,
        sessionmaker: sessionmaker = Provide[Container.db_client.provided.sessionmaker],
    ) -> None:
        async with sessionmaker() as session:
            result = await session.execute(select(TargetDB).where(TargetDB.id == id))
            target = result.scalar_one_or_none()
            if target:
                await session.delete(target)
                await session.commit()
