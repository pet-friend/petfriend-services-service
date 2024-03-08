from typing import Sequence

from fastapi import Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.service import Service, ServiceType
from app.models.stores import Store, StoreCreate
from app.models.util import Id
from app.repositories.services import ServicesRepository
from ..db import get_db
from .base_repository import BaseRepository
from .util import store_distance_filter


class StoresRepository(BaseRepository[Store, Id | str]):
    def __init__(
        self, session: AsyncSession = Depends(get_db), services_repo: ServicesRepository = Depends()
    ) -> None:
        super().__init__(Store, session)
        self.services_repo = services_repo

    async def create(self, data: StoreCreate, owner_id: Id) -> Store:
        service = Service(type=ServiceType.STORE)
        store = Store(**data.model_dump(), owner_id=owner_id, service=service)
        return await self.save(store)

    async def get_nearby(
        self, latitude: float, longitude: float, skip: int = 0, limit: int | None = None
    ) -> Sequence[Store]:
        query = (
            select(Store)
            .where(store_distance_filter(latitude, longitude))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(self, latitude: float, longitude: float) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(Store)
            .filter(store_distance_filter(latitude, longitude))
        )
        result = await self.db.exec(query)
        return result.one()

    async def get_by_name(self, name: str) -> Store | None:
        stores = await self.get_all(name=name)
        return stores[0] if len(stores) > 0 else None

    async def delete(self, record_id: Id | str) -> None:
        await self.services_repo.delete(record_id)
