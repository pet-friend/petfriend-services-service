from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import Store, StoreCreate
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository


class StoresRepository(BaseRepository[Store, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Store, session)

    async def create(self, data: StoreCreate) -> Store:
        return await self.save(Store.model_validate(data))

    async def get_by_name(self, name: str) -> Store | None:
        stores = await self.get_all(name=name)
        return stores[0] if len(stores) > 0 else None
