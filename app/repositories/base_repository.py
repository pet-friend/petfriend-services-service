from typing import Any, Sequence, Type, TypeVar, Generic
from abc import ABC
from sqlalchemy import ColumnExpressionArgument

from sqlmodel import AutoString, select, and_, func
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession

from app.exceptions.repository import RecordNotFound

T = TypeVar("T")  # Model
PK = TypeVar("PK")  # Primary key type


class BaseRepository(Generic[T, PK], ABC):
    def __init__(self, repositor_class: Type[T], session: AsyncSession):
        self.db = session
        self.cls = repositor_class

    def _common_filters(self, **filters: Any) -> ColumnExpressionArgument[bool] | bool:
        where_clauses = []
        for c, v in filters.items():
            if v is None:
                continue
            if not hasattr(self.cls, c):
                raise ValueError(f"Invalid column name: '{c}'")
            if isinstance(getattr(self.cls, c).type, AutoString):
                where_clauses.append(getattr(self.cls, c).ilike(f"%{v}%"))
            elif isinstance(v, list):
                where_clauses.append(getattr(self.cls, c).in_(v))
            else:
                where_clauses.append(getattr(self.cls, c) == v)

        if len(where_clauses) == 0:
            return True
        initial, *rest = where_clauses
        return and_(initial, *rest)

    def _list_select(self, **filters: Any) -> SelectOfScalar[T]:
        query = select(self.cls)
        return query.where(self._common_filters(**filters))

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
        query = query.where(self._common_filters(**filters))
        return query
