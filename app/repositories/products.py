from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.products import Product
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository


class ProductsRepository(BaseRepository[Product, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session)

    async def get_by_name(self, store_id: Id | str, name: str) -> Product | None:
        products = await self.get_all(store_id=store_id, name=name)
        return products[0] if len(products) > 0 else None
