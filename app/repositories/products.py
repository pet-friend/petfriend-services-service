from typing import Sequence

from fastapi import Depends
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.products import Product
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository
from .util import store_distance_filter


class ProductsRepository(BaseRepository[Product, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session)

    async def get_by_name(self, store_id: Id | str, name: str) -> Product | None:
        products = await self.get_all(store_id=store_id, name=name)
        return products[0] if len(products) > 0 else None

    async def get_nearby(
        self, latitude: float, longitude: float, skip: int = 0, limit: int | None = None
    ) -> Sequence[Product]:
        query = (
            select(Product)
            .where(Product.store.has(store_distance_filter(latitude, longitude)))  # type: ignore
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.exec(query)
        return result.all()

    async def count_nearby(self, latitude: float, longitude: float) -> int:
        query = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(Product)
            .filter(Product.store.has(store_distance_filter(latitude, longitude)))  # type: ignore
        )
        result = await self.db.exec(query)
        return result.one()
