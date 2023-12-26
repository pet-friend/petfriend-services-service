# mypy: ignore-errors
from typing import Sequence, Type, TypeVar, Generic
from abc import ABC

from sqlmodel import select, delete, and_, update
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.util import UUIDModel, Id

T = TypeVar("T", bound=UUIDModel)


class BaseRepository(Generic[T], ABC):
    def __init__(self, repositor_class: Type[T], session: AsyncSession):
        self.db = session
        self.cls = repositor_class

    def _list_select(self, **filters) -> SelectOfScalar:
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

    async def get_all(self, skip: int = 0, limit: int | None = None, **filters) -> Sequence[T]:
        query = self._list_select(**filters).offset(skip).limit(limit)
        result = await self.db.exec(query)
        return result.all()

    async def get_by_id(self, record_id: Id | str) -> T | None:
        return await self.db.get(self.cls, record_id)

    async def save(self, record: T) -> T:
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def update(self, record_id: Id | str, new_data: dict) -> T:
        existing = await self.get_by_id(record_id)
        if not existing:
            raise ValueError(f"Record with id {record_id} does not exist")
        query = update(self.cls).where(self.cls.id == record_id).values(**new_data)
        await self.db.exec(query)
        await self.db.refresh(existing)
        return existing

    async def delete(self, record_id: Id | str) -> None:
        query = delete(self.cls).where(self.cls.id == record_id)
        await self.db.exec(query)
