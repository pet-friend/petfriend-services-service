from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.stores import Store, StoreCreate

from ..db import get_db
from .base_repository import BaseRepository


class StoresRepository(BaseRepository[Store]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Store, session)

    async def create(self, data: StoreCreate) -> Store:
        return await self.save(Store.model_validate(data))

    async def get_by_name(self, name: str) -> Store | None:
        query = select(self.cls).where(self.cls.name == name)
        result = await self.db.exec(query)
        return result.first()
