from math import pi, radians, cos
from typing import Sequence, TypeVar

from fastapi import Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import SelectOfScalar

from app.models.service import Service, ServiceType
from app.models.stores import Store, StoreCreate
from app.models.addresses import Address
from app.models.util import Id
from app.repositories.services import ServicesRepository
from ..db import get_db
from .base_repository import BaseRepository


EARTH_RADIUS_KM = 6371.009
KM_PER_DEG_LAT = 2 * pi * EARTH_RADIUS_KM / 360.0

T = TypeVar("T")


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
        query = self.__distance_filter(select(Store), latitude, longitude).offset(skip).limit(limit)
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(self, latitude: float, longitude: float) -> int:
        query = self.__distance_filter(
            select(func.count()).select_from(Store),  # pylint: disable=not-callable
            latitude,
            longitude,
        )
        result = await self.db.exec(query)
        return result.one()

    async def get_by_name(self, name: str) -> Store | None:
        stores = await self.get_all(name=name)
        return stores[0] if len(stores) > 0 else None

    async def delete(self, record_id: Id | str) -> None:
        await self.services_repo.delete(record_id)

    def __distance_filter(
        self, query: SelectOfScalar[T], lat: float, long: float
    ) -> SelectOfScalar[T]:
        """
        Based on https://stackoverflow.com/a/5207131
        Should be decently accurate for small distances (a few km)
        """
        km_per_deg_long = KM_PER_DEG_LAT * cos(radians(lat))
        return query.filter(
            Store.service.has(  # type: ignore
                Service.address.has(  # type: ignore
                    func.pow(KM_PER_DEG_LAT * (Address.latitude - lat), 2)
                    + func.pow(km_per_deg_long * (Address.longitude - long), 2)
                    < func.pow(Store.delivery_range_km, 2)
                )
            )
        )
