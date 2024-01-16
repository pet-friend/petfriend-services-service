from typing import Any, Sequence, Type, TypeVar, Generic
from abc import ABC

from sqlmodel import select, and_, func
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions.repository import RecordNotFound

T = TypeVar("T")  # Model
PK = TypeVar("PK")  # Primary key type


class BaseRepository(Generic[T, PK], ABC):
    def __init__(self, repositor_class: Type[T], session: AsyncSession):
        self.db = session
        self.cls = repositor_class

    def _list_select(self, **filters: Any) -> SelectOfScalar[T]:
        query = select(self.cls)
        where_clauses = []
        for c, v in filters.items():
            if not hasattr(self.cls, c):
                raise ValueError(f"Invalid column name {c}")
            where_clauses.append(getattr(self.cls, c) == v)

        if len(where_clauses) == 0:
            return query

        initial, *rest = where_clauses
        return query.where(and_(initial, *rest))

    async def get_all(self, skip: int = 0, limit: int | None = None, **filters: Any) -> Sequence[T]:
        query = self._list_select(**filters).offset(skip).limit(limit)
        result = await self.db.exec(query)
        return result.all()

    async def get_by_id(self, record_id: PK) -> T | None:
        return await self.db.get(self.cls, record_id)

    async def save(self, record: T) -> T:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def update(self, record_id: PK, new_data: dict[str, Any]) -> T:
        existing = await self.get_by_id(record_id)
        if not existing:
            raise RecordNotFound
        for key, value in new_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        return await self.save(existing)

    async def delete(self, record_id: PK) -> None:
        existing = await self.get_by_id(record_id)
        if not existing:
            raise RecordNotFound
        await self.db.delete(existing)
        await self.db.flush()

    async def count_all(self, **filters: Any) -> int:
        query = self._count_select(**filters)
        result = await self.db.exec(query)
        return result.one()

    def _count_select(self, **filters: Any) -> SelectOfScalar[int]:
        # pylint bug: https://github.com/pylint-dev/pylint/issues/8138
        query = select(func.count()).select_from(self.cls)  # pylint: disable=not-callable

        # Applying filters, assuming keys in filters are column names of the Product model
        for key, value in filters.items():
            if hasattr(self.cls, key):
                query = query.where(getattr(self.cls, key) == value)

        return query
