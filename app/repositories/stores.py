# mypy: ignore-errors
from typing import Any
from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar
from sqlalchemy import func

from app.models.stores import Store, StoreCreate

from ..db import get_db
from .base_repository import BaseRepository


class StoresRepository(BaseRepository[Store]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Store, session)

    async def create(self, data: StoreCreate) -> Store:
        return await self.save(Store.model_validate(data))  # type: ignore

    async def get_by_name(self, name: str) -> Store | None:
        query = select(self.cls).where(self.cls.name == name)
        result = await self.db.exec(query)
        return result.first()

    async def count_all(self, **filters: Any) -> int:
        query = self._count_select(**filters)
        result = await self.db.exec(query)
        return result.one()

    def _count_select(self, **filters: Any) -> SelectOfScalar:
        # pylint: disable=not-callable
        query = select(func.count()).select_from(self.cls)

        # Applying filters, assuming keys in filters are column names of the Store model
        for key, value in filters.items():
            if hasattr(self.cls, key):
                query = query.where(getattr(self.cls, key) == value)

        return query
