from typing import Any

from fastapi import Depends
from sqlalchemy import ColumnExpressionArgument
from sqlmodel import and_
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stores import Category, Product, ProductCategories
from app.models.util import Id
from app.db import get_db
from ..nearby_repository import NearbyRepository
from ..util import product_distance_filter


class ProductsRepository(
    NearbyRepository[Product, tuple[Id | str, Id | str], [list[Category] | None]]
):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session, product_distance_filter, self.__get_extra_filters)

    async def get_by_name(self, store_id: Id | str, name: str) -> Product | None:
        products = await self.get_all(store_id=store_id, name=name)
        return products[0] if len(products) > 0 else None

    def __get_extra_filters(
        self, categories: list[Category] | None, **filters: Any
    ) -> ColumnExpressionArgument[bool] | bool:
        conditions = self._filters(**filters)
        if categories:
            conditions = and_(
                conditions,
                Product._categories.any(  # type: ignore
                    ProductCategories.category.in_(categories)  # type: ignore
                ),
            )
        return conditions
