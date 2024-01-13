from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.products import Product
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository


class ProductsRepository(BaseRepository[Product, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Product, session)
