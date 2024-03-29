# pylint: disable=duplicate-code
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.purchases import Purchase
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository


class PurchasesRepository(BaseRepository[Purchase, tuple[Id | str, Id | str]]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Purchase, session)
