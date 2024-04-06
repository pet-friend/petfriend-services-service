from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import Store
from app.models.util import Id
from app.db import get_db
from ..nearby_repository import NearbyRepository
from ..util import store_distance_filter


class StoresRepository(NearbyRepository[Store, Id | str, []]):
    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        super().__init__(Store, session, store_distance_filter)

    async def get_by_name(self, name: str) -> Store | None:
        stores = await self.get_all(name=name)
        return stores[0] if len(stores) > 0 else None
