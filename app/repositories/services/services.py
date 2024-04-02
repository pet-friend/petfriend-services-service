from typing import Sequence

from fastapi import Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.services import Service
from app.models.util import Id
from app.db import get_db
from app.repositories.util import service_distance_filter
from ..base_repository import BaseRepository


class ServicesRepository(BaseRepository[Service, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        super().__init__(Service, session)

    async def get_nearby(
        self, latitude: float, longitude: float, skip: int = 0, limit: int | None = None
    ) -> Sequence[Service]:
        query = (
            select(Service)
            .where(service_distance_filter(latitude, longitude))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(self, latitude: float, longitude: float) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(Service)
            .filter(service_distance_filter(latitude, longitude))
        )
        result = await self.db.exec(query)
        return result.one()
