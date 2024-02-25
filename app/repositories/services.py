from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.service import Service
from app.models.util import Id
from ..db import get_db
from .base_repository import BaseRepository


class ServicesRepository(BaseRepository[Service, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Service, session)
