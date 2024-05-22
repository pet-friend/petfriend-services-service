from typing import Any, Sequence, Type, TypeVar, Generic
from abc import ABC

from sqlmodel import AutoString, select, and_, func
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import asc, desc, ColumnExpressionArgument
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty

from app.exceptions.repository import RecordNotFound
from app.models.util import SortOrder

T = TypeVar("T")  # Model
PK = TypeVar("PK")  # Primary key type


class BaseRepository(Generic[T, PK], ABC):
    def __init__(self, repositor_class: Type[T], session: AsyncSession):
        self.db = session
        self.cls = repositor_class

    def _common_filters(self, **filters: Any) -> ColumnExpressionArgument[bool] | bool:
        where_clauses = []
        col_name: str
        for col_name, v in filters.items():
            if v is None:
                continue

            other_col_name = None
            if "." in col_name:
                col_name, other_col_name = col_name.split(".", maxsplit=1)

            col = self._get_column(col_name)
            if other_col_name and isinstance(col.comparator, RelationshipProperty.Comparator):
                # This is a relationship column
                other_cls = col.comparator.entity.class_
                other_col = self._get_column(other_col_name, cls=other_cls)
                where_clauses.append(col.has(other_col == v))
            elif isinstance(col.type, AutoString):
                where_clauses.append(col.ilike(f"%{v}%"))
            elif isinstance(v, list):
                where_clauses.append(col.in_(v))
            else:
                where_clauses.append(col == v)

        if len(where_clauses) == 0:
            return True
        initial, *rest = where_clauses
        return and_(initial, *rest)

    def _list_select(self, **filters: Any) -> SelectOfScalar[T]:
        query = select(self.cls)
        return query.where(self._common_filters(**filters))

    async def get_all(
        self,
        skip: int = 0,
        limit: int | None = None,
        sort_by: str | None = None,
        sort_order: SortOrder = SortOrder.ASCENDING,
        **filters: Any,
    ) -> Sequence[T]:
        query = self._list_select(**filters)
        order_func = asc if sort_order == SortOrder.ASCENDING else desc
        if sort_by is not None:
            self._get_column(sort_by)
            query = query.order_by(order_func(getattr(self.cls, sort_by)))
        query = query.offset(skip).limit(limit)
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

    def _get_column(
        self, col_name: str, cls: Type[Any] | None = None
    ) -> InstrumentedAttribute[Any]:
        cls = cls or self.cls
        if not hasattr(cls, col_name):
            raise ValueError(f"Invalid column name for {cls}: '{col_name}'")
        return getattr(cls, col_name)
