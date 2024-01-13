from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.addresses import Address
from app.models.util import Id

from ..db import get_db
from .base_repository import BaseRepository


class AddressesRepository(BaseRepository[Address, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Address, session)
