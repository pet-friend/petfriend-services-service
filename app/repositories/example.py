from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from ..models.example import Example, ExampleCreate
from ..db import get_db
from .base_repository import BaseRepository


class ExampleCrud(BaseRepository[Example]):
    def __init__(self, session: AsyncSession = Depends(get_db)):
        super().__init__(Example, session)

    async def create(self, data: ExampleCreate) -> Example:
        return await self.save(Example.model_validate(data))
