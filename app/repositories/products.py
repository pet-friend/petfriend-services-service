from fastapi import Depends
from sqlmodel import select, col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.products import Product, ProductCreate

from ..db import get_db
from .base_repository import BaseRepository


class ProductsRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session)

    async def create(self, data: ProductCreate) -> Product:
        return await self.save(Product.model_validate(data))

    async def get_by_name(self, name: str) -> Product | None:
        query = select(self.cls).where(col(self.cls.name) == name)
        result = await self.db.exec(query)
        return result.first()
