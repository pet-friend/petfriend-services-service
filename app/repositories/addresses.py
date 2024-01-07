from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.addresses import Address

from ..db import get_db
from .base_repository import BaseRepository


class AddressesRepository(BaseRepository[Address]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Address, session)
