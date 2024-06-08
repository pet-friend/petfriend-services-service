from typing import Any, Callable, Generic, Protocol, Sequence, Type, TypeVar, ParamSpec

from sqlalchemy import ColumnExpressionArgument, Exists
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from .base_repository import BaseRepository

T = TypeVar("T")  # Model
PK = TypeVar("PK")  # Primary key type

P = ParamSpec("P")


class ExtraFilterGetter(Protocol[P]):
    def __call__(*args: P.args, **kwargs: Any) -> ColumnExpressionArgument[bool] | bool: ...


class NearbyRepository(BaseRepository[T, PK], Generic[T, PK, P]):
    def __init__(
        self,
        repository_class: Type[T],
        session: AsyncSession,
        distance_filter: Callable[[float, float], Exists],
        extra_filter_getter: ExtraFilterGetter[P] | None = None,
    ) -> None:
        super().__init__(repository_class, session)
        self.distance_filter = distance_filter
        self.extra_filter_getter = extra_filter_getter or self._common_filters

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        *args: P.args,
        skip: int = 0,
        limit: int | None = None,
        **kwargs: Any
    ) -> Sequence[T]:
        query = (
            select(self.cls)
            .where(self.__filters(latitude, longitude, *args, **kwargs))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(
        self, latitude: float, longitude: float, *args: P.args, **kwargs: Any
    ) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(self.cls)
            .filter(self.__filters(latitude, longitude, *args, **kwargs))
        )
        result = await self.db.exec(query)
        return result.one()

    def __filters(
        self, latitude: float, longitude: float, *args: P.args, **kwargs: Any
    ) -> ColumnExpressionArgument[bool]:
        cond: ColumnExpressionArgument[bool] = self.distance_filter(latitude, longitude)
        if self.extra_filter_getter:
            cond = and_(cond, self.extra_filter_getter(*args, **kwargs))
        return cond
