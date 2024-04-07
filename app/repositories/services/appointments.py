from typing import Sequence, Any
from datetime import datetime

from fastapi import Depends
from sqlmodel import and_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.services import Appointment
from app.models.util import Id
from app.db import get_db
from ..base_repository import BaseRepository


class AppointmentsRepository(BaseRepository[Appointment, Id | str]):
    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        super().__init__(Appointment, session)

    async def get_all_by_range(
        self,
        range_start: datetime,
        range_end: datetime,
        skip: int = 0,
        limit: int | None = None,
        **filters: Any
    ) -> Sequence[Appointment]:
        """
        Return all of the appointments that take place (totally or partially) in the given range.
        `range_start` and `range_end` must be timezone-aware datetimes.
        """
        # TZDateTime handles converting the aware datetimes to UTC
        query = select(Appointment)
        where = self._common_filters(**filters)
        where = and_(Appointment.start < range_end, Appointment.end > range_start, where)
        query = query.where(where).offset(skip).limit(limit)
        result = await self.db.exec(query)
        return result.all()
