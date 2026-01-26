from collections.abc import AsyncGenerator
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class IDBClient(Protocol):
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]: ...
