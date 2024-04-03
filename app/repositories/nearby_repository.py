from typing import Callable, Sequence, Type, TypeVar

from sqlalchemy import Exists
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from .base_repository import BaseRepository

T = TypeVar("T")  # Model
PK = TypeVar("PK")  # Primary key type


class NearbyRepository(BaseRepository[T, PK]):
    def __init__(
        self,
        repository_class: Type[T],
        session: AsyncSession,
        distance_filter: Callable[[float, float], Exists],
    ) -> None:
        super().__init__(repository_class, session)
        self.distance_filter = distance_filter

    async def get_nearby(
        self, latitude: float, longitude: float, skip: int = 0, limit: int | None = None
    ) -> Sequence[T]:
        query = (
            select(self.cls)
            .where(self.distance_filter(latitude, longitude))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(self, latitude: float, longitude: float) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.cls)
            .filter(self.distance_filter(latitude, longitude))
        )
        result = await self.db.exec(query)
        return result.one()
