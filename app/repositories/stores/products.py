# pylint: disable=duplicate-code
from typing import Any, Sequence

from fastapi import Depends
from sqlalchemy import ColumnExpressionArgument
from sqlmodel import select, func, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import Category, Product, ProductCategories
from app.models.util import Id
from app.db import get_db
from ..base_repository import BaseRepository
from ..util import store_distance_filter


# TODO: Change NearbyRepository so that we can use it with products too
class ProductsRepository(BaseRepository[Product, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session)

    async def get_by_name(self, store_id: Id | str, name: str) -> Product | None:
        products = await self.get_all(store_id=store_id, name=name)
        return products[0] if len(products) > 0 else None

    def __nearby_filter(
        self,
        latitude: float,
        longitude: float,
        categories: list[Category] | None = None,
        **filters: Any
    ) -> ColumnExpressionArgument[bool]:
        conditions = Product.store.has(store_distance_filter(latitude, longitude))  # type: ignore
        if categories:
            conditions = and_(
                conditions,
                Product._categories.any(  # type: ignore
                    ProductCategories.category.in_(categories)  # type: ignore
                ),
            )
        conditions = and_(conditions, self._filters(**filters))
        return conditions

    async def get_nearby(
        self,
        latitude: float,
        longitude: float,
        categories: list[Category] | None = None,
        skip: int = 0,
        limit: int | None = None,
        **filters: Any
    ) -> Sequence[Product]:
        query = (
            select(Product)
            .where(self.__nearby_filter(latitude, longitude, categories, **filters))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(
        self,
        latitude: float,
        longitude: float,
        categories: list[Category] | None = None,
        **filters: Any
    ) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(Product)
            .filter(self.__nearby_filter(latitude, longitude, categories, **filters))
        )
        result = await self.db.exec(query)
        return result.one()
